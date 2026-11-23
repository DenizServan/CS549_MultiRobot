"""
CHECK the link perception -> pick (pick.getGrasp, pick.fingersHold): would the grasp computed from a wrist read hold
the piece? This is the question behind every "the fingers miss the piece" in the spell log.

    python3 checks/check_grasp.py --reader cnn                  20 close views over random pieces, seed 0
    python3 checks/check_grasp.py --reader cnn --n 40

For each view: the free wrist-like camera is put CLOSE_VIEW_HEIGHTS above a random piece (like the wrist looks in
pick.py), the picture is read, the read nearest the piece is taken, and its grasp is compared with the TRUE grasp:
    xy err     grasp point error            (fingersHold needs < GRASP_TOL_XY = 1.5 cm)
    axis err   closing axis error, either way round (needs < GRASP_TOL_ANGLE_DEG = 15°)
    z err      gripper height error         (needs < GRASP_TOL_Z = 1.5 cm)
    holds      fingersHold() itself, i.e. what pick.py would decide

What correct looks like: every read that is right AND accepted (conf >= CONF_ACCEPT) holds. A right, accepted read
that does not hold means the pose (refine.py) or the grasp height (pick.getTopHeightAt) is off, not the symbol.
"""
import numpy as np
from common import getArgs, makeScene, getClassifier, angleDiffDeg, prm, loadTemplates
from evaluate import placeCamera
from reader import readPicture
from ground_truth import isRight, getTruth
import motion_parameters as mp
from pick import getGrasp, fingersHold, getTopHeightAt

args = getArgs(lambda ap: ap.add_argument("--n", type=int, default=20, help="number of close views"))
args.kind = "close"
s = makeScene(args)
C, floor_z, view, cam = s["C"], s["floor_z"], s["view"], prm.TEST_WRIST_CAMERA_NAME
templates = loadTemplates()
classifier = getClassifier(args.reader)
rng = np.random.default_rng(args.seed + 1)
truth = getTruth(C, s["names"])

print(f"\n{'piece':>14s} {'true':>4s} {'read':>4s} {'conf':>6s} {'ok':>3s} {'acc':>3s} {'xy err':>7s} {'axis err':>8s} "
      f"{'z err':>6s} holds")
stats = []
for i in rng.choice(len(truth), size=min(args.n, len(truth)), replace=False):
    p = truth[i]
    cam_xy = p["xy"] + rng.normal(0., prm.CLOSE_VIEW_OFFSET_STD, 2)
    placeCamera(C, cam, cam_xy, p["z"] + prm.PIECE_THICKNESS + rng.uniform(*prm.CLOSE_VIEW_HEIGHTS), rng.uniform(-np.pi, np.pi))
    reads = [r for r in readPicture(view, C, cam, templates, floor_z, classifier)
             if np.linalg.norm(r["xy"] - p["xy"]) < mp.WRIST_MATCH_DISTANCE]
    if not reads:
        print(f"{p['name']:>14s} {p['symbol']:>4s}    -  (no read within WRIST_MATCH_DISTANCE)")
        continue
    r = max(reads, key=lambda r: r["conf"])
    gxy, closing = getGrasp(r, templates)
    true_xy, true_closing = getGrasp({"symbol": p["symbol"], "xy": p["xy"], "yaw": p["yaw"]}, templates)
    z = getTopHeightAt({"view": view, "C": C}, cam, gxy, r) - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN
    frame = C.getFrame(p["name"])
    k = p["k"]
    true_top = (frame.getPosition() + frame.getRotationMatrix() @ np.r_[templates["grasp"][k][0], prm.PIECE_THICKNESS])[2]
    z_err = z - (true_top - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN)
    a = angleDiffDeg(closing, true_closing)
    axis_err = min(a, 180 - a)
    holds = fingersHold(C, gxy, closing, z, p, templates)
    ok, acc = isRight(r, p, templates), r["conf"] >= prm.CONF_ACCEPT
    stats.append((ok, acc, holds))
    print(f"{p['name']:>14s} {p['symbol']:>4s} {r['symbol']:>4s} {r['conf']:6.3f} {'y' if ok else 'n':>3s} "
          f"{'y' if acc else 'n':>3s} {100 * np.linalg.norm(gxy - true_xy):5.1f}cm {axis_err:7.1f}° "
          f"{100 * z_err:5.1f}cm {holds}")

st = np.array(stats, bool).reshape(-1, 3)
good = st[:, 0] & st[:, 1]
print(f"\n{len(st)} reads: {st[:, 0].sum()} right, {st[:, 1].sum()} accepted, {good.sum()} right and accepted, "
      f"of those {(good & st[:, 2]).sum()} hold. Accepted but wrong: {(st[:, 1] & ~st[:, 0]).sum()}")
