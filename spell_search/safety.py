# Ground-truth collision monitor (evaluation only, the robots never read it).
#
# The task itself is kinematic and the planners treat the pieces as non-colliding (world.py turns their
# contacts off). This monitor keeps a separate copy of the scene in which the pieces DO collide, syncs it
# with the world every MONITOR_EVERY steps and counts contact episodes (a pair that starts touching):
#
#   robot_robot     any part of p1 against any part of p2 (bases, arms, grippers)   -> must stay 0
#   robot_static    a robot against a table or a wall (a base on the floor is fine)   -> must stay 0
#   arm_piece       an arm / gripper against a piece it is not picking               -> knocks pieces in reality
#   arm_target      the fingers against the piece they are picking (closing on it)   -> expected, kinematic grasp
#   held_piece      a held piece against something else than its own gripper        -> e.g. dragged over pieces
#   base_piece      a base driving over a piece lying on the floor                    -> known simplification
#
# Only penetrations deeper than MONITOR_DEPTH count (pieces lying on each other touch at ~0 mm).
import os
import tempfile
import numpy as np
import robotic as ry
from config import *

CATS = ("robot_robot", "robot_static", "arm_piece", "arm_target", "held_piece", "base_piece")


class CollisionMonitor:
    def __init__(self, world):
        self.W = W = world
        # an independent copy through a .g file: addConfigurationCopy shares the shapes with the world, so
        # turning contacts on in such a copy would turn them on in every planner copy too (IK became 60x slower)
        fd, fn = tempfile.mkstemp(suffix=".g")
        os.write(fd, str(W.C.write()).encode())
        os.close(fd)
        self.C = ry.Config()
        self.C.addFile(fn)
        os.remove(fn)
        self.piece_of = {}
        for n in W.pieces:
            for ch in self.C.getFrame(n).getChildren():
                if ch.getShapeType() == ry.ST.ssBox:
                    ch.setContact(1)
                    self.piece_of[ch.name] = n
        self.C.processStructure()       # without it getCollisions fails after changing contacts (robotic 0.4.1)
        # processStructure re-orders the frames: map the world's frame order onto the copy's
        idx = {n: i for i, n in enumerate(W.C.getFrameNames())}
        self.perm = np.array([idx[n] for n in self.C.getFrameNames()])
        self.active = {}                # contact episodes going on: key -> event
        self.events = []                # [t start, category, robot, a, b, deepest penetration]
        self.attached = []              # (t, robot, piece) from world.attach

    def robot_of(self, name):
        for r in ROBOTS:
            if name.startswith(f"{r}_") or name == BASE[r]:
                return r
        return None

    def classify(self, a, b):
        """category and robot of a contact pair, or None if it does not involve a robot or a held piece"""
        W = self.W
        ra, rb = self.robot_of(a), self.robot_of(b)
        pa, pb = self.piece_of.get(a), self.piece_of.get(b)
        if pa is not None and pa == pb:
            return None                                     # strokes of the same piece overlap at the joints
        if ra and rb:
            return ("robot_robot", ra) if ra != rb else None
        if ra or rb:
            r, own, other, piece = (ra, a, b, pb) if ra else (rb, b, a, pa)
            if piece is None:
                if other == "floor" and own == BASE[r]:
                    return None
                return "robot_static", r
            held = [rr for rr in ROBOTS if W.holding[rr] == piece]
            if held:
                return (None if held[0] == r else ("held_piece", held[0]))
            if own == BASE[r]:
                return "base_piece", r
            return "arm_piece", r                           # split into arm_target / arm_piece in summary()
        # no robot part: a held piece against a table, a wall or another piece
        for r in ROBOTS:
            h = W.holding[r]
            if h is not None and h in (pa, pb):
                other = b if pa == h else a
                if other == "floor" or self.piece_of.get(other) is not None or other.startswith("table") or other.startswith("wall"):
                    return "held_piece", r
        return None

    def check(self):
        W = self.W
        self.C.setFrameState(W.C.getFrameState()[self.perm])
        self.C.computeCollisions()
        now = {}
        for a, b, d in self.C.getCollisions(-MONITOR_DEPTH):
            c = self.classify(a, b)
            if c is None:
                continue
            cat, r = c
            pair = tuple(sorted((self.piece_of.get(a) or a, self.piece_of.get(b) or b)))   # one key per piece, any order
            key = (cat, r) + pair
            ev = now.get(key) or self.active.get(key)
            if ev is None:                                  # a new contact episode
                ev = [round(W.t, 2), cat, r, pair[0], pair[1], 0.]
                self.events.append(ev)
            ev[5] = max(ev[5], round(-d, 4))                # deepest penetration during the episode
            now[key] = ev
        self.active = now

    def summary(self):
        """contact episodes and deepest penetration (m) per category; an arm contact with a piece the same
        robot picks up within 10 s is arm_target"""
        out = {c: 0 for c in CATS}
        depth = {c: 0. for c in CATS}
        seen = set()
        for t, cat, r, a, b, d in self.events:
            if cat == "arm_piece":
                piece = a if a in self.W.symbol else b
                if any(rr == r and n == piece and t - 1. <= ta <= t + 10. for ta, rr, n in self.attached):
                    cat = "arm_target"
            # one count per (category, robot, pair) and contact episode; arm_target once per piece
            k = (cat, r, a, b) if cat == "arm_target" else None
            if k is not None and k in seen:
                continue
            if k is not None:
                seen.add(k)
            out[cat] += 1
            depth[cat] = max(depth[cat], d)
        return out, depth
