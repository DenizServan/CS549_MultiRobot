"""
Picking one piece: drive next to it, re-read it with the wrist camera, grasp it at the READ pose.
All actions are generators (one small motion step per next(), see arm.py); `world` is the dict spell.py builds:
{"C", "view", "templates", "classifier", "floor_z", "names", "entries"}.

    getGrasp(read, templates)                    ->  (grasp point xy, closing angle) in the room for a read
    driveNextTo(world, robot, xy)                generator -> True if the base now stands PICK_DISTANCE from xy
    lookClosely(world, robot, read)              generator -> (most confident wrist read near the target, camera)
    pickPiece(world, robot, entry, symbol)       generator -> (held piece info, "") or (None, reason)
    inspectPiece(world, robot, entry)            generator -> reason ("" if the wrist read it confidently)

Grasping is attach(): the fingers are not simulated. Whether they would close on the piece is decided with the ground
truth (gripper close enough to the TRUE grasp point, axis and height); that is the only use of the truth here.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from reader import readPicture
from camera import takePicture
from ground_truth import getTruth
from confidence import wrapAngle
from arm import getJointIndices, moveArm, getArmIK, goHome, Blocked
from base import driveTo, isFree, getBasePose, copyWithBase
from piece_map import updateMap
from clearance import claim


def getGrasp(read, templates):
    """
    Returns (grasp point xy, closing angle) in the room: the symbol's grasp marker moved by the read pose.
    """
    k = templates["symbols"].index(read["symbol"])
    g_xy, g_angle = templates["grasp"][k]
    c, s = np.cos(read["yaw"]), np.sin(read["yaw"])
    return np.asarray(read["xy"]) + np.array([[c, -s], [s, c]]) @ np.asarray(g_xy), read["yaw"] + g_angle


def scan(world, robot, camera):
    """
    Reads one picture of `camera` and merges it into the shared map (forgetting what the picture no longer shows).
    Returns the reads.
    """
    reads = readPicture(world["view"], world["C"], camera, world["templates"], world["floor_z"], world["classifier"])
    updateMap(world["entries"], reads, world["C"], camera)
    return reads


def getTopHeightAt(world, camera, xy, read):
    """
    Returns the height of the piece's top face at xy from the camera's point cloud: the median height of the points
    within GRASP_TOL_XY of xy and not above the read's top (a leaning piece is not level). Falls back to read["z_top"].
    """
    _, points, valid, _ = takePicture(world["view"], world["C"], camera)
    near = valid & (np.linalg.norm(points[:, :2] - xy, axis=1) < mp.GRASP_TOL_XY) & (points[:, 2] < read["z_top"] + .005)
    return float(np.median(points[near, 2])) if near.sum() >= 3 else read["z_top"]


def getTruePiece(read, truth):
    """
    Returns the true piece under a read: within MATCH_DISTANCE in xy, and of those the one whose top is closest in
    height (the pieces of a pile have nearly the same xy). None if none.
    """
    near = [p for p in truth if np.linalg.norm(p["xy"] - read["xy"]) < prm.MATCH_DISTANCE]
    return min(near, key=lambda p: abs(p["z"] + prm.PIECE_THICKNESS - read["z_top"])) if near else None


def fingersHold(C, grasp_xy, closing, z, piece, templates):
    """
    True if fingers closing at (grasp_xy, z) along `closing` would hold the true piece: near its true grasp point, with
    its closing axis (either direction), at the height of its top face there (pieces can lean).
    """
    k = templates["symbols"].index(piece["symbol"])
    frame = C.getFrame(piece["name"])
    true_xy, true_closing = getGrasp({"symbol": piece["symbol"], "xy": piece["xy"], "yaw": piece["yaw"]}, templates)
    top = frame.getPosition() + frame.getRotationMatrix() @ np.r_[templates["grasp"][k][0], prm.PIECE_THICKNESS]
    a = abs(wrapAngle(closing - true_closing))
    return (np.linalg.norm(grasp_xy - true_xy) < mp.GRASP_TOL_XY and np.degrees(min(a, np.pi - a)) < mp.GRASP_TOL_ANGLE_DEG
            and abs(z - (top[2] - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN)) < mp.GRASP_TOL_Z)


def driveNextTo(world, robot, xy):
    """
    Generator: drives the base to a free spot PICK_DISTANCE from xy, facing it, from which the arm reaches above it.
    Spots are tried around xy, the one on the line from the base first. The spot is claimed (the other robot plans
    around it). Returns True if the base got there.
    """
    C = world["C"]
    here = getBasePose(C, robot)
    a0 = np.arctan2(here[1] - xy[1], here[0] - xy[0])
    turns = [0] + [s * j for j in range(1, mp.PICK_TRIES) for s in (1, -1)]
    for a in a0 + np.radians(360 / mp.PICK_TRIES) * np.array(turns[:mp.PICK_TRIES]):
        b = xy + mp.PICK_DISTANCE * np.array([np.cos(a), np.sin(a)])
        if not isFree(C, robot, b):
            continue
        Cp = copyWithBase(C, robot, b, a + np.pi)
        if getArmIK(Cp, robot, [xy[0], xy[1], 0.3], [np.cos(a), np.sin(a)], mp.ARM_HOME) is None:
            continue
        claim(robot, xy, b)
        if (yield from driveTo(C, robot, b, a + np.pi)):
            return True
    return False


def lookClosely(world, robot, read, match_distance=mp.WRIST_MATCH_DISTANCE):
    """
    Generator: wrist-camera looks at a read, in the order of WRIST_LOOKS (height above the piece top, sideways shift),
    until one gives a read within match_distance of read["xy"] with conf >= CONF_ACCEPT. Every look updates the map.
    Returns (the most confident read near the target or None, camera name of the picture it came from).
    """
    C = world["C"]
    _, arm_idx = getJointIndices(C, robot)
    phi = getBasePose(C, robot)[2]
    side = np.array([np.cos(phi + np.pi / 2), np.sin(phi + np.pi / 2)])
    camera = prm.WRIST_CAMERA_PATTERN.format(robot=robot)
    best = None
    for height, shift in mp.WRIST_LOOKS:
        q_view = getArmIK(C, robot, [*(read["xy"] + shift * side), read["z_top"] + height], side, C.getJointState()[arm_idx])
        if q_view is None:
            continue
        yield from moveArm(C, robot, q_view)
        reads = scan(world, robot, camera)
        near = [r for r in reads if np.linalg.norm(r["xy"] - read["xy"]) < match_distance]
        if near:
            r = max(near, key=lambda r: r["conf"])
            if best is None or r["conf"] > best["conf"]:
                best = r
        if best is not None and best["conf"] >= prm.CONF_ACCEPT:
            break
    return best, camera


def inspectPiece(world, robot, entry):
    """
    Generator: drives next to a piece nobody could read and looks at it with the wrist camera (the reads go into the
    map). Every entry around it (the wrist reads may have made new ones for the same piece) counts as inspected, so it
    is not inspected again. Returns "" if it now reads confidently, else the reason.
    """
    xy = entry["read"]["xy"]
    entry["tries"] += 1
    try:
        if not (yield from driveNextTo(world, robot, xy)):
            return "no spot to stand"
        best, _ = yield from lookClosely(world, robot, entry["read"])
    except Blocked:
        best = None
    for e in world["entries"]:
        if np.linalg.norm(e["read"]["xy"] - xy) < mp.SPREAD_PIECE_RADIUS:
            e["tries"] = max(e["tries"], 1)
    yield from goHome(world["C"], robot)
    if best is None or best["conf"] < prm.CONF_ACCEPT:
        return "still not readable"
    return ""


def pickPiece(world, robot, entry, symbol):
    """
    Generator: goes to a map entry believed to be `symbol`, checks it with the wrist camera and grasps it at the read
    pose. Returns ({"name", "read", "grasp_xy", "hold", "z"}, "") when the piece is held (lifted), else (None, reason).
    A failure is written into the map entry (a ruled-out symbol, or one more failed try).
    """
    C, templates = world["C"], world["templates"]
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    _, arm_idx = getJointIndices(C, robot)
    read = entry["read"]
    try:
        if not (yield from driveNextTo(world, robot, getGrasp(read, templates)[0])):
            entry["tries"] += 1
            return None, "no spot to stand"

        # wrist camera: the piece must read as the wanted symbol, confidently (looks: far, closer, from the side)
        best, camera = yield from lookClosely(world, robot, read)
        if best is None or best["conf"] < prm.CONF_ACCEPT or best["symbol"] != symbol:
            if best is not None and best["conf"] >= prm.CONF_ACCEPT:
                entry["ruled_out"].add(symbol)              # a sure read of another symbol
            entry["tries"] += 1
            yield from goHome(C, robot)
            seen = "nothing readable" if best is None else f"'{best['symbol']}' (conf {best['conf']:.2f})"
            return None, f"wrist camera sees {seen}"
        read = best

        # grasp at the read pose (the gripper is symmetric: two ways to hold the same grasp)
        grasp_xy, closing = getGrasp(read, templates)
        z = getTopHeightAt(world, camera, grasp_xy, read) - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN
        for flip in (0., np.pi):
            d = [np.cos(closing + flip), np.sin(closing + flip)]
            q_pre = getArmIK(C, robot, [*grasp_xy, z + mp.PRE_GRASP_LIFT], d, C.getJointState()[arm_idx])
            q_grasp = None if q_pre is None else getArmIK(C, robot, [*grasp_xy, z], d, q_pre)
            if q_grasp is not None:
                break
        if q_grasp is None:
            entry["tries"] += 1
            yield from goHome(C, robot)
            return None, "no arm solution for the grasp"
        yield from moveArm(C, robot, q_pre)
        yield from moveArm(C, robot, q_grasp)
        piece = getTruePiece(read, getTruth(C, world["names"]))
        if piece is None or not fingersHold(C, grasp_xy, closing, z, piece, templates):
            entry["tries"] += 1
            yield from moveArm(C, robot, q_pre, max_wait=None)
            yield from goHome(C, robot)
            return None, "the fingers miss the piece"
        C.attach(gripper, piece["name"])
        yield from moveArm(C, robot, q_pre, max_wait=None)
        return {"name": piece["name"], "read": read, "grasp_xy": grasp_xy, "hold": closing + flip, "z": z}, ""
    except Blocked:
        entry["tries"] += 1
        yield from goHome(C, robot)
        return None, "the other robot was in the way"
