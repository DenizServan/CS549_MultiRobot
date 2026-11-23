"""
Placing the held piece upright in a table cell. Actions are generators (one small motion step per next()).

    putDown(C, robot, piece_name, surface, place_xy, z, hold, turn)   generator -> True if the piece is down
    placePiece(world, robot, held, table, cell_xy)                     generator -> "" if placed, else the reason
    settleFreePieces(world)                                           PhysX settle of every piece no gripper holds

The piece is turned using its READ yaw and put where its READ pose says its centre will land on the cell, so any
perception error stays visible in the final pose. Afterwards PhysX lets the pieces settle.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from scene_builder import settlePieces
from confidence import wrapAngle
from arm import getJointIndices, moveArm, getArmIK, goHome, Blocked
from base import driveTo, copyWithBase
from clearance import claim
from table import getTableTop, getStandSpots


def rotate(yaw, v):
    """
    Returns the 2D vector v turned by yaw.
    """
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[c, -s], [s, c]]) @ np.asarray(v)


def getPlaceTarget(read, templates, cell_xy):
    """
    Returns (grasp point xy at the cell, turn): where the grasp point must go so that the piece, turned to UPRIGHT_YAW,
    has its centre (stroke centroid) on the cell, and the turn from the read yaw. Both from the READ pose.
    """
    k = templates["symbols"].index(read["symbol"])
    g_xy, _ = templates["grasp"][k]
    origin = np.asarray(cell_xy) - rotate(mp.UPRIGHT_YAW, templates["centroid"][k])
    return origin + rotate(mp.UPRIGHT_YAW, g_xy), wrapAngle(mp.UPRIGHT_YAW - read["yaw"])


def putDown(C, robot, piece_name, surface, place_xy, z, hold, turn):
    """
    The gripper holds the piece (lifted), closing axis at angle `hold`. Brings the grasp point to place_xy, turned by
    `turn`, puts it down at height z and attaches it to `surface`. The last arm joint turns at most ~2.9 rad, so if
    the whole turn has no IK solution: turn half, put it down, grasp it again from the other side (same grasp, gripper
    turned by 180 deg) and turn the rest. Generator; returns True if the piece is down.
    """
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    _, arm_idx = getJointIndices(C, robot)

    def goDown(angle, now):
        """IK above and at place_xy for closing angle `angle`, the gripper now at angle `now`; KOMO starts from the
        last arm joint turned by the difference, one way or the other (it is what turns the gripper about the
        vertical)."""
        d = [np.cos(angle), np.sin(angle)]
        for sign in (1., -1.):
            q0 = C.getJointState()[arm_idx]
            q0[6] = np.clip(q0[6] + sign * wrapAngle(angle - now), -mp.LAST_JOINT_LIMIT, mp.LAST_JOINT_LIMIT)
            q_up = getArmIK(C, robot, [*place_xy, z + mp.PRE_GRASP_LIFT], d, q0)
            q_down = None if q_up is None else getArmIK(C, robot, [*place_xy, z], d, q_up)
            if q_down is not None:
                return q_up, q_down
        return None

    for _ in range(3):
        qs = goDown(hold + turn, hold)
        if qs is not None:
            yield from moveArm(C, robot, qs[0])
            yield from moveArm(C, robot, qs[1])
            C.attach(surface, piece_name)
            yield from moveArm(C, robot, qs[0], max_wait=None)
            return True
        half = goDown(hold + turn / 2, hold)
        if half is None:
            return False
        yield from moveArm(C, robot, half[0])
        yield from moveArm(C, robot, half[1])
        C.attach(surface, piece_name)                       # let go
        yield from moveArm(C, robot, half[0], max_wait=None)
        now = hold + turn / 2
        hold, turn = now + np.pi, turn / 2                  # grasp again from the other side
        again = goDown(hold, now)
        if again is None:
            return False
        yield from moveArm(C, robot, again[0])
        yield from moveArm(C, robot, again[1])
        C.attach(gripper, piece_name)
        yield from moveArm(C, robot, again[0], max_wait=None)
    return False


def settleFreePieces(world):
    """
    Lets PhysX settle every piece that no gripper holds, starting where they are (drop 0: pieces lying still stay).
    """
    C = world["C"]
    held = lambda n: C.getFrame(n).getParent() is not None and C.getFrame(n).getParent().name.endswith("_gripper")
    free = [n for n in world["names"] if not held(n)]
    settlePieces(C, free, prm.STATIC_OBSTACLE_NAMES, drop=0.)


def placePiece(world, robot, held, table, cell_xy):
    """
    Generator: drives to a side of the table from which the arm reaches the cell, puts the held piece down upright on
    the cell and lets PhysX settle the pieces. If no side can be used right now (the other robot stands, works or
    drives there), it keeps holding the piece, waits PLACE_WAIT_STEPS and tries again, up to PLACE_TRIES times.
    Returns "" if placed, else the reason (the piece is then let go where it is).
    """
    C, templates = world["C"], world["templates"]
    target_xy, turn = getPlaceTarget(held["read"], templates, cell_xy)
    z = getTableTop(C, table) + prm.PIECE_THICKNESS - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN + mp.PLACE_CLEARANCE
    for _ in range(mp.PLACE_TRIES):
        reason = "no side of the table reaches the cell"
        try:
            for spot in getStandSpots(C, robot, table, cell_xy):
                Cp = copyWithBase(C, robot, spot[:2], spot[2])
                if getArmIK(Cp, robot, [*target_xy, z + mp.PRE_GRASP_LIFT], [np.cos(spot[2]), np.sin(spot[2])], mp.ARM_HOME) is None:
                    continue
                claim(robot, cell_xy, spot[:2])
                if not (yield from driveTo(C, robot, spot[:2], spot[2])):
                    reason = "no path to the table"
                    continue
                if (yield from putDown(C, robot, held["name"], table, target_xy, z, held["hold"], turn)):
                    reason = ""
                    break
                reason = "no arm solution for putting it down"
                break                                       # waiting would not change that
        except Blocked:
            reason = "the other robot was in the way"
        if reason in ("", "no arm solution for putting it down"):
            break
        print(f"[{robot}]     cannot place yet ({reason}), holding the piece and waiting")
        claim(robot)                                        # blocked for now: free our claims, hold on, try again
        yield from goHome(C, robot)
        for _ in range(mp.PLACE_WAIT_STEPS):
            yield
    if reason:
        C.attach(prm.FLOOR_FRAME_NAME, held["name"])        # let go: it falls where it is
    yield from goHome(C, robot)
    settleFreePieces(world)
    return reason
