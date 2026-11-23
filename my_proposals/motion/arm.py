"""
The robot's joints and arm motions.

Motions are GENERATORS: each `next()` takes one small step (both robots step in turn, spell.py), so a motion is used
as `yield from moveArm(...)` inside another generator. Before every step the robot checks the clearance to the other
robot (clearance.py) and waits if the step would bring them too close.

    getJointIndices(C, robot)                              ->  (base indices, arm indices) in C.getJointState()
    moveJoints(C, idx, target, step_sizes, max_wait)       generator: straight line in joint space, in small steps
    moveArm(C, robot, q, max_wait) / goHome(C, robot)      generators for the 7 arm joints
    getArmIK(C, robot, position, closing_dir, q_start)     ->  7 arm joints (KOMO) or None
    runToEnd(C, generator, show)                           runs one generator alone (debugging), returns its result
"""
import os
import sys
import time
import numpy as np
import robotic as ry #type: ignore

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from clearance import getMinGap


class Blocked(Exception):
    """The other robot stayed in the way for longer than the motion was allowed to wait."""


def getJointIndices(C, robot):
    """
    Returns (base indices, arm indices) of the robot's joints in C.getJointState(): base x, y, yaw and 7 arm joints.
    """
    names = C.getJointNames()
    base = prm.ROBOT_BASE[robot]
    return [names.index(f"{base}:{i}") for i in range(3)], [names.index(f"{robot}_panda_joint{i}") for i in range(1, 8)]


def moveJoints(C, idx, target, step_sizes, max_wait=mp.MAX_WAIT_STEPS):
    """
    Generator: moves only the joints idx to target in a straight line in joint space, no joint changing more than
    step_sizes per step. A step is taken only if the robots stay SAFETY_MARGIN apart afterwards (or get farther
    apart than they were); otherwise this step waits. Raises Blocked after max_wait waiting steps in a row
    (max_wait None: wait as long as it takes).
    """
    start = C.getJointState()[idx]
    target = np.asarray(target, float)
    n = max(1, int(np.ceil(np.max(np.abs(target - start) / step_sizes))))
    s, waited = 1, 0
    while s <= n:
        q = C.getJointState()                               # read fresh: the other robot moves in between
        before, gap_before = q[idx].copy(), getMinGap(C)
        q[idx] = start + (target - start) * s / n
        C.setJointState(q)
        gap = getMinGap(C)
        if gap >= mp.SAFETY_MARGIN or gap > gap_before:
            s, waited = s + 1, 0
        else:                                               # too close to the other robot: undo and wait
            q[idx] = before
            C.setJointState(q)
            waited += 1
            if max_wait is not None and waited > max_wait:
                raise Blocked()
        yield


def moveArm(C, robot, q, max_wait=mp.MAX_WAIT_STEPS):
    """
    Generator: the robot's 7 arm joints to q (steps of at most MAX_JOINT_STEP).
    """
    yield from moveJoints(C, getJointIndices(C, robot)[1], q, mp.MAX_JOINT_STEP, max_wait)


def runToEnd(C, generator, show=True):
    """
    Runs one motion generator to the end on its own (for debugging a single action) and returns its result.
    """
    while True:
        try:
            next(generator)
        except StopIteration as done:
            return done.value
        if show:
            C.view(False)
            time.sleep(mp.STEP_TIME)


def getArmIK(C, robot, position, closing_dir, q_start):
    """
    KOMO, one time slice: arm joints that put the gripper at `position`, pointing down, closing axis along closing_dir
    (xy), starting the search from q_start. The base stays where it is. Returns the 7 arm joints or None.
    """
    Cp = ry.Config()
    Cp.addConfigurationCopy(C)
    _, arm_idx = getJointIndices(Cp, robot)
    q = Cp.getJointState()
    q[arm_idx] = q_start
    Cp.setJointState(q)
    Cp.selectJoints([f"{robot}_panda_joint{i}" for i in range(1, 8)])
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    k = ry.KOMO(Cp, 1, 1, 0, False)
    k.addControlObjective([], 0, 1e-1)
    k.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq, [1e1])
    k.addObjective([], ry.FS.position, [gripper], ry.OT.eq, [1e1], list(position))
    k.addObjective([], ry.FS.vectorZ, [gripper], ry.OT.eq, [1e1], [0., 0., 1.])
    k.addObjective([], ry.FS.vectorX, [gripper], ry.OT.eq, [1e1], [closing_dir[0], closing_dir[1], 0.])
    ret = ry.NLP_Solver(k.nlp(), verbose=0).setOptions(stopTolerance=1e-3).solve()
    if ret.eq > mp.IK_TOLERANCE or ret.ineq > mp.IK_TOLERANCE:
        return None
    return k.getPath()[0].copy()


def goHome(C, robot):
    """
    Generator: arm to ARM_HOME (the pose for driving). Waits as long as needed (folding the arm never gets stuck for
    good: the other robot also folds its arm when it gives up).
    """
    yield from moveArm(C, robot, mp.ARM_HOME, max_wait=None)
