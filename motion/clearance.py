"""
Keeping the two robots apart. Both move kinematically in small steps (arm.moveJoints); before every step the moving
robot checks that it stays clear of the other one, otherwise it waits.

    getBalls(C, robot)              ->  list of (centre xyz, radius) covering the robot: base, arm, held piece
    getMinGap(C)                    ->  smallest gap between the two robots' balls (a step needs >= SAFETY_MARGIN)
    claim(robot, work_xy, base_xy)  remembers where a robot is about to work / stand (the other one keeps away)
    getOtherClaims(C, robot)        ->  list of xy the OTHER robots occupy or have claimed (base now, base goal, work)
    isFarFromOthers(C, robot, xy)   ->  True if xy is CLAIM_DISTANCE from all of those
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp

CLAIMS = {}                               # robot -> {"work": xy or None, "base": xy or None}


def getBalls(C, robot):
    """
    Returns balls (centre, radius) covering the robot: one around the base, one on every arm joint and one half-way
    between neighbouring joints, one on the gripper, and one around a piece the gripper holds.
    """
    base = C.getFrame(prm.ROBOT_BASE[robot]).getPosition()
    balls = [(base, mp.BASE_BALL_RADIUS)]
    gripper = C.getFrame(prm.GRIPPER_FRAME_PATTERN.format(robot=robot))
    joints = [C.getFrame(f"{robot}_panda_joint{i}").getPosition() for i in range(1, 8)] + [gripper.getPosition()]
    for a, b in zip(joints[:-1], joints[1:]):
        balls += [(a, mp.LINK_BALL_RADIUS), ((a + b) / 2, mp.LINK_BALL_RADIUS)]
    balls.append((joints[-1], mp.LINK_BALL_RADIUS))
    for child in gripper.getChildren():                     # a held piece is attached to the gripper
        if prm.CHARACTER_FRAME_PREFIX in child.name:
            balls.append((child.getPosition(), mp.HELD_BALL_RADIUS))
    return balls


def getGap(C, robot_a, robot_b):
    """
    Returns the smallest gap (meters, negative = overlap) between the balls of two robots.
    """
    A, B = getBalls(C, robot_a), getBalls(C, robot_b)
    ca, ra = np.array([c for c, _ in A]), np.array([r for _, r in A])
    cb, rb = np.array([c for c, _ in B]), np.array([r for _, r in B])
    d = np.linalg.norm(ca[:, None, :] - cb[None, :, :], axis=2) - ra[:, None] - rb[None, :]
    return float(d.min())


def getMinGap(C):
    """
    Returns the smallest gap between any two robots (inf if all bases are farther apart than CHECK_DISTANCE).
    """
    gap = np.inf
    for i, a in enumerate(mp.ROBOTS):
        for b in mp.ROBOTS[i + 1:]:
            pa = C.getFrame(prm.ROBOT_BASE[a]).getPosition()[:2]
            pb = C.getFrame(prm.ROBOT_BASE[b]).getPosition()[:2]
            if np.linalg.norm(pa - pb) < mp.CHECK_DISTANCE:
                gap = min(gap, getGap(C, a, b))
    return gap


def claim(robot, work_xy=None, base_xy=None):
    """
    Remembers where `robot` is about to work (a piece, a viewpoint) and where its base will stand. None clears it.
    """
    CLAIMS[robot] = {"work": None if work_xy is None else np.asarray(work_xy, float),
                     "base": None if base_xy is None else np.asarray(base_xy, float)}


def getOtherClaims(C, robot):
    """
    Returns the xy points the other robots occupy or have claimed while they work on something: their base now, their
    base goal, their work point. An idle robot claims nothing (it is only an obstacle for driving, base.py).
    """
    points = []
    for other in mp.ROBOTS:
        c = CLAIMS.get(other, {})
        claimed = [p for p in (c.get("work"), c.get("base")) if p is not None]
        if other != robot and claimed:
            points += [C.getFrame(prm.ROBOT_BASE[other]).getPosition()[:2]] + claimed
    return points


def isFarFromOthers(C, robot, xy, distance=mp.CLAIM_DISTANCE):
    """
    True if xy is at least `distance` from every point the other robots occupy or have claimed.
    """
    return all(np.linalg.norm(np.asarray(xy) - p) >= distance for p in getOtherClaims(C, robot))
