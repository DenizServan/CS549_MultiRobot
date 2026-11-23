"""
Two robots spell a word at the same time, each on its own table: p1 puts the first half of the word on table_left,
p2 the second half on table_right. Both move kinematically, step by step in turn (one small step of p1, one of p2,
...), and never come closer than SAFETY_MARGIN to each other (clearance.py: a step that would, waits).

    python3 motion/spell.py                                    CNN reader, seed 0, word ROBOTICS, viewer
    python3 motion/spell.py --word "HELLO" --reader template --seed 3
    python3 motion/spell.py --headless                         no viewer

The scene is the one task scene (perception/scene_builder.buildScene): every symbol once plus the word's letters twice
more, some pieces in piles, the rest scattered, some near the walls.
Each robot, whenever it is free, picks its next action for its next letter (nextAction), in this order:
    1. fetch    a map entry read as the letter: drive there, wrist look, grasp, put it upright in the next cell
    2. explore  drive to the nearest viewpoint nobody scanned yet and scan with the mast camera
    3. spread   take the top piece off a pile, put it down alone and read it there
    4. inspect  look with the wrist camera at a lone piece nobody could read
    5. wait     if the only work left is next to the other robot; otherwise give the letter up
A robot that is done drives back to its start spot, so it does not stand in the other robot's way.
Every action is a generator (one small motion step per next()); the map of pieces is shared by both robots, and a
robot never starts work within CLAIM_DISTANCE of where the other robot works or stands (claims, clearance.py).

Files: arm.py (joints, KOMO, stepwise motions), base.py (driving), clearance.py (keeping the robots apart), table.py
(cells), piece_map.py (shared memory of reads), pick.py, place.py, spread.py, geo_grasp.py, score.py (truth check at
the end), motion_parameters.py (every number).
"""
import os
import sys
import time
import argparse
import numpy as np
import robotic as ry #type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
PERCEPTION = os.path.join(os.path.dirname(HERE), "perception")
sys.path.insert(0, PERCEPTION)
sys.path.insert(0, HERE)
import parameters as prm
import motion_parameters as mp
from scene_builder import buildScene
from templates import loadTemplates
from classify_template import classifyTemplate
from base import driveTo, getBasePose, isFree
from table import getCells
from piece_map import findPiece, findUnreadable, removeNear, getViewpoints
from pick import pickPiece, inspectPiece, scan
from place import placePiece
from spread import getSpreadEntry, spreadPiece
from score import scoreTable
from clearance import claim, isFarFromOthers, getMinGap


def getClassifier(name):
    """
    Returns the perception classifier: the CNN or the template matcher.
    """
    if name == "cnn":
        sys.path.insert(0, os.path.join(PERCEPTION, "cnn"))
        from classify_cnn import CnnClassifier
        return CnnClassifier()
    return classifyTemplate


# ------------------------------------------- 1. ACTIONS (generators that return (text, placed)) -------------------------

def fetchAction(world, robot, state, entry, letter):
    held, reason = yield from pickPiece(world, robot, entry, letter)
    if held is None:
        return f"pick failed: {reason}", False
    removeNear(world["entries"], held["read"]["xy"])
    reason = yield from placePiece(world, robot, held, state["table"], state["cells"][state["i"]])
    return ("placed in cell " + str(state["i"] + 1)) if not reason else "not placed: " + reason, not reason


def exploreAction(world, robot, viewpoint):
    C = world["C"]
    claim(robot, viewpoint, viewpoint)
    if not (yield from driveTo(C, robot, viewpoint, getBasePose(C, robot)[2])):
        return "viewpoint not reachable", False
    return "scanned from a new viewpoint", False


def spreadAction(world, robot, entry):
    symbol, reason = yield from spreadPiece(world, robot, entry)
    if reason:
        return f"spreading a pile failed: {reason}", False
    return f"took a piece off a pile, it reads '{symbol}'" if symbol else "took a piece off a pile, not readable", False


def inspectAction(world, robot, entry):
    reason = yield from inspectPiece(world, robot, entry)
    return "looked at an unreadable piece: " + (reason if reason else f"now read"), False


def parkAction(world, robot, home):
    C = world["C"]
    claim(robot, None, home)
    ok = yield from driveTo(C, robot, home, getBasePose(C, robot)[2])
    return "parked out of the way" if ok else "could not reach the parking spot", False


def waitAction(steps):
    for _ in range(steps):
        yield
    return "waited for the other robot", False


# ------------------------------------------- 2. CHOOSING THE NEXT ACTION -----------------------------------------------

def getViewpoint(world, robot):
    """
    Returns (and removes from the shared list) the nearest viewpoint the base can stand on that is away from the
    other robot, or None.
    """
    C = world["C"]
    here = getBasePose(C, robot)[:2]
    ok = [v for v in world["viewpoints"] if isFree(C, robot, v) and isFarFromOthers(C, robot, v)]
    if not ok:
        return None
    v = min(ok, key=lambda p: np.linalg.norm(p - here))
    world["viewpoints"] = [p for p in world["viewpoints"] if p is not v]
    return v


def nextAction(world, robot, state, other_busy):
    """
    Returns (text, generator, entry) for the robot's next action (see the top of the file), or None when the robot is
    done (all its letters placed or given up, or MAX_ACTIONS used).
    """
    C = world["C"]
    while state["i"] < len(state["letters"]) and state["actions"] < mp.MAX_ACTIONS:
        letter = state["letters"][state["i"]]
        here = getBasePose(C, robot)[:2]
        entry = findPiece(C, world["entries"], letter, here, robot)
        if entry is not None:
            r = entry["read"]
            return (f"'{letter}': fetching the read at ({r['xy'][0]:.2f}, {r['xy'][1]:.2f}), conf {r['conf']:.2f}",
                    fetchAction(world, robot, state, entry, letter), entry)
        v = getViewpoint(world, robot)
        if v is not None:
            return f"'{letter}': not on the map, exploring ({v[0]:.1f}, {v[1]:.1f})", exploreAction(world, robot, v), None
        entry = getSpreadEntry(world, here, robot)
        if entry is not None:
            return f"'{letter}': spreading a pile", spreadAction(world, robot, entry), entry
        entry = findUnreadable(C, world["entries"], here, robot)
        if entry is not None:
            return f"'{letter}': inspecting an unreadable piece", inspectAction(world, robot, entry), entry
        if other_busy and state["waits"] < mp.MAX_WAIT_ACTIONS:
            state["waits"] += 1
            return f"'{letter}': nothing to do away from the other robot, waiting", waitAction(50), None
        print(f"[{robot}] '{letter}': given up")
        state["i"] += 1
    return None


# ------------------------------------------- 3. RUNNING BOTH ROBOTS -----------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--word", default=prm.WORD)
    ap.add_argument("--reader", choices=["template", "cnn"], default="cnn")
    ap.add_argument("--seed", type=int, default=prm.RANDOM_SEED)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    show = not args.headless
    prm.CONF_ACT, prm.CONF_VERIFY, prm.CONF_ACCEPT = prm.READER_THRESHOLDS[args.reader]   # this reader's thresholds

    C, names, floor_z, _ = buildScene(args.word, args.seed, verbose=True)
    world = {"C": C, "view": ry.CameraView(C), "templates": loadTemplates(), "classifier": getClassifier(args.reader),
             "floor_z": floor_z, "names": names, "entries": [], "viewpoints": getViewpoints(C), "dropped": []}
    letters = [ch for ch in args.word.upper() if ch != " "]
    half = (len(letters) + 1) // 2
    states = {}
    for robot, part in zip(mp.ROBOTS, (letters[:half], letters[half:])):
        cells = getCells(C, mp.TABLES[robot])
        if len(part) > len(cells):
            raise ValueError(f"{len(part)} letters for {robot} but only {len(cells)} reachable cells")
        states[robot] = {"table": mp.TABLES[robot], "letters": part, "cells": cells, "i": 0, "actions": 0,
                         "waits": 0, "placed": 0, "parked": False, "home": getBasePose(C, robot)[:2]}
        scan(world, robot, prm.MAST_CAMERA_PATTERN.format(robot=robot))
    if show:
        C.view(False, f"spelling '{args.word}': {args.reader} reader, seed {args.seed}")

    t0, steps, min_gap = time.time(), 0, np.inf
    active = {r: None for r in mp.ROBOTS}                   # robot -> (text, generator, entry) of its current action
    while steps < mp.MAX_STEPS:
        busy = False
        for robot in mp.ROBOTS:
            if active[robot] is None:
                others_busy = any(active[o] is not None and "waiting" not in active[o][0] for o in mp.ROBOTS if o != robot)
                active[robot] = nextAction(world, robot, states[robot], others_busy)
                if active[robot] is None and not states[robot]["parked"]:    # done: drive back to the start spot
                    states[robot]["parked"] = True                          # so it is not in the other one's way
                    active[robot] = ("done, driving back to its start spot",
                                     parkAction(world, robot, states[robot]["home"]), None)
                if active[robot] is None:
                    continue
                text, _, entry = active[robot]
                states[robot]["actions"] += 1
                if entry is not None:
                    entry["claimed"] = robot
                print(f"[{time.time() - t0:6.1f} s, step {steps:5d}] [{robot}] {text}")
            busy = True
            try:
                next(active[robot][1])
            except StopIteration as done:
                text, placed = done.value
                entry = active[robot][2]
                if entry is not None:
                    entry["claimed"] = None
                claim(robot)                                # the robot no longer works anywhere
                scan(world, robot, prm.MAST_CAMERA_PATTERN.format(robot=robot))
                if placed:
                    states[robot]["i"] += 1
                    states[robot]["placed"] += 1
                if not text.startswith("waited"):
                    print(f"[{time.time() - t0:6.1f} s, step {steps:5d}] [{robot}]     -> {text}")
                active[robot] = None
        if not busy:
            break
        steps += 1
        min_gap = min(min_gap, getMinGap(C))
        if show:
            C.view(False)
            time.sleep(mp.STEP_TIME)

    print(f"\nspelled '{args.word}' ({len(names)} pieces) in {time.time() - t0:.0f} s, {steps} steps; "
          f"smallest gap between the robots: {100 * min_gap:.0f} cm (SAFETY_MARGIN {100 * mp.SAFETY_MARGIN:.0f} cm)")
    total = 0
    for robot in mp.ROBOTS:
        s = states[robot]
        rows = scoreTable(C, names, s["cells"], s["letters"], world["templates"])
        print(f"{robot} on {s['table']} ({s['actions']} actions):")
        for i, r in enumerate(rows):
            detail = f"yaw err {r['yaw_err']:5.1f} deg, centre {100 * r['pos_err']:4.1f} cm" if "yaw_err" in r else "empty"
            print(f"  cell {i + 1}: '{r['want']}' -> '{r['got']}'  {detail}  {'OK' if r['ok'] else 'WRONG'}")
        total += sum(r["ok"] for r in rows)
    print(f"correct cells: {total}/{len(letters)}")
    if show:
        C.view(True, "done (press a key to close)")
