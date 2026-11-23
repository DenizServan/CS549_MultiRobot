"""
CHECK clearance.py / base.driveTo / arm.moveJoints: two robots whose paths cross never come closer than SAFETY_MARGIN.

    python3 checks/check_clearance.py              viewer
    python3 checks/check_clearance.py --headless

Test 1 (crossing): p1 drives from its start to (-2, -2) while p2 drives from its start to (-2, 2); the paths cross.
Test 2 (arm in the way): p2 parks and stretches its arm sideways; p1 drives past it close by.
Printed per test: smallest gap between the robots (must stay >= SAFETY_MARGIN), steps, whether both arrived.
What to look for in the viewer: one robot stops and waits (or re-plans) while the other passes.
"""
import os
import sys
import time
import argparse
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "perception"))
sys.path.insert(0, os.path.join(ROOT, "motion"))
import parameters as prm
import motion_parameters as mp
from scene_builder import buildScene
from base import driveTo, getBasePose
from arm import moveArm
from clearance import claim, getMinGap


def runTogether(C, gens, show):
    """
    Steps all generators in turn (like spell.py) until all are done. Returns (results, steps, smallest gap).
    """
    results, steps, gap = [None] * len(gens), 0, np.inf
    active = list(range(len(gens)))
    while active:
        for i in list(active):
            try:
                next(gens[i])
            except StopIteration as done:
                results[i] = done.value
                active.remove(i)
        steps += 1
        gap = min(gap, getMinGap(C))
        if show:
            C.view(False)
            time.sleep(mp.STEP_TIME)
    return results, steps, gap


ap = argparse.ArgumentParser()
ap.add_argument("--headless", action="store_true")
args = ap.parse_args()
show = not args.headless
C, names, floor_z, _ = buildScene(prm.WORD, 0, cameras=(), verbose=False)
if show:
    C.view(False, "clearance test")

goals = {"p1": np.array([-2., -2.]), "p2": np.array([-2., 2.])}
for r, g in goals.items():
    claim(r, g, g)
res, steps, gap = runTogether(C, [driveTo(C, r, goals[r], 0.) for r in mp.ROBOTS], show)
print(f"test 1 (crossing paths): arrived {res}, {steps} steps, smallest gap {100 * gap:.1f} cm "
      f"(must be >= {100 * mp.SAFETY_MARGIN:.0f})")
for r in mp.ROBOTS:
    claim(r)

# test 2: p2 parks at (0, 0) and stretches its arm towards +y (as when picking a piece; it claims the arm's work point),
# then p1 drives from where it is to (0, 2.5), past p2's arm
q_stretch = [np.pi / 2, 0.6, 0., -1.2, 0., 1.8, 0.]
park = np.array([0., 0.])
claim("p2", None, park)
res2, _, _ = runTogether(C, [driveTo(C, "p2", park, 0.)], show)
res3, _, _ = runTogether(C, [moveArm(C, "p2", q_stretch)], show)
tip = C.getFrame(prm.GRIPPER_FRAME_PATTERN.format(robot="p2")).getPosition()[:2]
claim("p2", tip, park)
res4, steps, gap = runTogether(C, [driveTo(C, "p1", np.array([0., 2.5]), 0.)], show)
print(f"test 2 (arm in the way): p2 parked {res2}, arm tip at ({tip[0]:.2f}, {tip[1]:.2f}), p1 arrived {res4}, "
      f"{steps} steps, smallest gap {100 * gap:.1f} cm")
if show:
    C.view(True, "done (press a key)")
