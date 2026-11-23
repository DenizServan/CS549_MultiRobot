"""
Spreading piles: pieces in a pile are hard to read (they touch, lean and cover each other) but easy to read alone.
So a robot takes the top pieces off a pile one by one with a geometric grasp (no symbol needed), puts each down on
free floor, and reads it there with the wrist camera. Actions are generators (one small motion step per next()).

    isInPile(C, entry, robot)                ->  True if the entry is the top of a pile worth taking off
    getSpreadEntry(world, xy, robot)         ->  the pile entry to take off next, or None
    spreadPiece(world, robot, entry)         generator -> (symbol read at the new spot or None, reason if failed)
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from scene_builder import getKeepOutBoxes, getOutsideKeepOut, getRoomLimits
from arm import getJointIndices, moveArm, getArmIK, goHome, Blocked
from base import getBasePose
from place import putDown, settleFreePieces
from piece_map import removeNear, isUsable
from pick import driveNextTo, lookClosely
from geo_grasp import getGeometricGrasp, getHeldPiece
from clearance import isFarFromOthers


def isInPile(C, entry, robot, dropped=()):
    """
    True if a read is the top of a pile and worth taking off: it lies on another piece (stacked) or leans (tilted beyond
    MAX_TILT_DEG, so it cannot be read where it is), nothing lies on it (not occluded), it was not put down alone
    already, the robot may work on it (piece_map.isUsable), and no robot had to drop a piece back there
    MAX_TRIES_PER_PIECE times already (dropped: xy of those drops; the re-read piece would be a new map entry).
    """
    r = entry["read"]
    on_pile = r["stacked"] or r["tilt"] > np.radians(prm.MAX_TILT_DEG)
    drops = sum(np.linalg.norm(r["xy"] - d) < mp.SPREAD_PIECE_RADIUS for d in dropped)
    return on_pile and not r["occluded"] and not entry["alone"] and isUsable(C, entry, robot) and \
        drops < mp.MAX_TRIES_PER_PIECE


def getSpreadEntry(world, xy, robot):
    """
    Returns the pile entry (isInPile) nearest to xy, or None.
    """
    pile = [e for e in world["entries"] if isInPile(world["C"], e, robot, world.get("dropped", []))]
    return min(pile, key=lambda e: np.linalg.norm(e["read"]["xy"] - xy)) if pile else None


def getSetAsideSpot(world, robot, z, closing):
    """
    Returns a floor point SET_ASIDE_REACHES from the base (the farther ring first): inside the room, away from tables
    and bases, away from where the other robot works (CLAIM_DISTANCE), at least SET_ASIDE_MIN_GAP from every piece on
    the map (the farthest such point first), and where the gripper reaches both above it and down at height z with
    this closing angle (what putDown needs; checking only above it chose spots the arm could not reach down to).
    None if none.
    """
    C = world["C"]
    _, arm_idx = getJointIndices(C, robot)
    base = getBasePose(C, robot)[:2]
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    boxes = getKeepOutBoxes(C)
    seen = np.array([e["read"]["xy"] for e in world["entries"]]).reshape(-1, 2)
    r = prm.LETTER_RADIUS
    d = [np.cos(closing), np.sin(closing)]
    for reach in mp.SET_ASIDE_REACHES:
        spots = []
        for a in np.linspace(-np.pi, np.pi, mp.SET_ASIDE_TRIES, endpoint=False):
            p = base + reach * np.array([np.cos(a), np.sin(a)])
            gap = np.min(np.linalg.norm(seen - p, axis=1)) if len(seen) else 1.
            if x_min + r < p[0] < x_max - r and y_min + r < p[1] < y_max - r and getOutsideKeepOut(p[0], p[1], boxes) \
                    and gap >= mp.SET_ASIDE_MIN_GAP and isFarFromOthers(C, robot, p):
                spots.append((gap, p))
        for _, p in sorted(spots, key=lambda s: -s[0]):
            q_up = getArmIK(C, robot, [*p, z + mp.PRE_GRASP_LIFT], d, C.getJointState()[arm_idx])
            if q_up is not None and getArmIK(C, robot, [*p, z], d, q_up) is not None:
                return p
    return None


def spreadPiece(world, robot, entry):
    """
    Generator: takes the piece of a pile entry off the pile: drives next to it, finds a geometric grasp in a wrist
    picture, grasps it (attach; the ground truth decides whether the fingers hold it), puts it down on free floor,
    lets PhysX settle, and reads it there (the read goes into the map). Returns (symbol read there or None, reason if
    it failed).
    """
    C, floor_z = world["C"], world["floor_z"]
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    camera = prm.WRIST_CAMERA_PATTERN.format(robot=robot)
    xy = entry["read"]["xy"]
    entry["tries"] += 1
    name = None
    try:
        if not (yield from driveNextTo(world, robot, xy)):
            return None, "no spot to stand"
        phi = getBasePose(C, robot)[2]
        side = [np.cos(phi + np.pi / 2), np.sin(phi + np.pi / 2)]
        q_view = getArmIK(C, robot, [*xy, entry["read"]["z_top"] + mp.WRIST_LOOKS[0][0]], side, mp.ARM_HOME)
        if q_view is None:
            return None, "cannot look at it"
        yield from moveArm(C, robot, q_view)
        grasp = getGeometricGrasp(world["view"], C, camera, xy, floor_z)
        if grasp is None:
            yield from goHome(C, robot)
            return None, "no free straight stroke to grasp"
        g_xy, closing, top = grasp
        z = top - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN
        _, arm_idx = getJointIndices(C, robot)
        for flip in (0., np.pi):
            d = [np.cos(closing + flip), np.sin(closing + flip)]
            q_pre = getArmIK(C, robot, [*g_xy, z + mp.PRE_GRASP_LIFT], d, C.getJointState()[arm_idx])
            q_grasp = None if q_pre is None else getArmIK(C, robot, [*g_xy, z], d, q_pre)
            if q_grasp is not None:
                break
        if q_grasp is None:
            yield from goHome(C, robot)
            return None, "no arm solution for the grasp"
        yield from moveArm(C, robot, q_pre)
        yield from moveArm(C, robot, q_grasp)
        name = getHeldPiece(C, world["names"], world["templates"], g_xy, closing, z)
        if name is None:
            yield from moveArm(C, robot, q_pre, max_wait=None)
            yield from goHome(C, robot)
            return None, "the fingers miss the piece"
        C.attach(gripper, name)
        yield from moveArm(C, robot, q_pre, max_wait=None)

        # put it down on free floor
        z_floor = floor_z + prm.PIECE_THICKNESS - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN + mp.SET_ASIDE_CLEARANCE
        spot = getSetAsideSpot(world, robot, z_floor, closing + flip)
        down = spot is not None and (yield from putDown(C, robot, name, prm.FLOOR_FRAME_NAME, spot, z_floor,
                                                        closing + flip, 0.))
    except Blocked:
        down = False
        if name is None:                                    # nothing in the gripper yet
            yield from goHome(C, robot)
            return None, "the other robot was in the way"
    if not down:
        C.attach(prm.FLOOR_FRAME_NAME, name)               # let go where it is: it falls (back) onto the pile
        world.setdefault("dropped", []).append(np.asarray(g_xy))   # do not try this pile spot forever
    removeNear(world["entries"], xy)
    yield from goHome(C, robot)
    settleFreePieces(world)
    if not down:
        return None, "could not put it down alone (dropped it)"

    # read it alone (spot is where its grasp point went down: its origin lies up to SPREAD_PIECE_RADIUS away);
    # only the entry of THIS piece is marked alone (never spread again)
    try:
        best, _ = yield from lookClosely(world, robot, {"xy": spot, "z_top": floor_z + prm.PIECE_THICKNESS},
                                         mp.SPREAD_PIECE_RADIUS)
    except Blocked:
        best = None
    for e in world["entries"]:
        if np.linalg.norm(e["read"]["xy"] - spot) < mp.SPREAD_PIECE_RADIUS:
            e["alone"] = True
    yield from goHome(C, robot)
    if best is None or best["conf"] < prm.CONF_ACCEPT:
        return None, ""
    return best["symbol"], ""
