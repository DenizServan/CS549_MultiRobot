"""
CHECK step 9 (reader.py, whole pipeline): every read of one picture next to the truth.

    python3 checks/check_reads.py                                   far view, template reader
    python3 checks/check_reads.py --reader cnn --kind close --pile
    python3 checks/check_reads.py --reader cnn --x 1.0 --y -1.5

Top view: true pieces in grey with their symbol; each read as an arrow (its yaw) at its origin with its symbol:
    green  = right and trusted           orange = right but not trusted (only costs time)
    red    = WRONG and trusted (the dangerous case: the robot acts on it)
    purple = wrong and not trusted       x      = read matched no true piece (phantom)
Trusted = conf >= CONF_ACT for far views, >= CONF_ACCEPT for close views (as in evaluate.py).

What correct looks like: no red; orange only on cut / covered / tilted pieces; pose errors of right reads ~1 cm and
a few degrees (pick.py needs < GRASP_TOL_XY = 1.5 cm at the grasp point and < 15° on the closing axis).
"""
import numpy as np
import matplotlib.pyplot as plt
from common import getArgs, makeScene, getClassifier, nearestTruth, angleDiffDeg, prm, loadTemplates
from reader import readPicture
from ground_truth import matchRead, isRight

args = getArgs()
s = makeScene(args)
C, floor_z, truth = s["C"], s["floor_z"], s["truth"]
templates = loadTemplates()
reads = readPicture(s["view"], C, s["camera"], templates, floor_z, getClassifier(args.reader))
limit = prm.CONF_ACT if args.kind == "far" else prm.CONF_ACCEPT

print(f"\n{len(reads)} reads, trusted if conf >= {limit} ({'CONF_ACT' if args.kind == 'far' else 'CONF_ACCEPT'})\n")
print(f"{'read':>4s} {'sym':>3s} {'true':>4s} {'conf':>6s} {'xy err':>7s} {'yaw err':>7s} {'flags':22s} verdict")
fig, ax = plt.subplots(figsize=(10, 10))
for p in truth:
    ax.plot(*p["xy"], "o", color="0.8", ms=14)
    ax.text(p["xy"][0], p["xy"][1], p["symbol"], ha="center", va="center", fontsize=9, color="0.4")
counts = {}
for i, r in enumerate(reads):
    piece = matchRead(r, truth)
    right, trusted = isRight(r, piece, templates), r["conf"] >= limit
    verdict = ("right, trusted" if right and trusted else "right, not trusted" if right else
               "WRONG, TRUSTED" if trusted else "wrong, not trusted")
    if piece is None:
        verdict += " (phantom: no true piece within 5 cm)"
    counts[verdict.split(" (")[0]] = counts.get(verdict.split(" (")[0], 0) + 1
    flags = ",".join(f for f in ("cut", "occluded", "stacked") if r[f]) + (f" tilt{np.degrees(r['tilt']):.0f}"
                                                                         if r["tilt"] > np.radians(5) else "")
    p, d = (piece, np.linalg.norm(piece["xy"] - r["xy"])) if piece else nearestTruth(r["xy"], truth)
    print(f"{i:4d} {r['symbol']:>3s} {p['symbol']:>4s} {r['conf']:6.3f} {100 * d:5.1f}cm "
          f"{angleDiffDeg(r['yaw'], p['yaw']):6.1f}° {flags:22s} {verdict}")
    colour = "green" if right and trusted else "orange" if right else "red" if trusted else "purple"
    ax.arrow(r["xy"][0], r["xy"][1], .08 * np.cos(r["yaw"]), .08 * np.sin(r["yaw"]), color=colour, width=.004)
    ax.text(r["xy"][0] + .03, r["xy"][1] + .03, f"{r['symbol']} {r['conf']:.2f}", color=colour, fontsize=8)
    if piece is None:
        ax.plot(*r["xy"], "x", color=colour, ms=10)
print("\nsummary:", counts)
pts = np.array([r["xy"] for r in reads]) if reads else s["cam_xy"][None]
ax.set_xlim(pts[:, 0].min() - .4, pts[:, 0].max() + .4)
ax.set_ylim(pts[:, 1].min() - .4, pts[:, 1].max() + .4)
ax.set_aspect("equal")
ax.set_title("reads vs truth (arrow = read yaw: the piece frame's x axis)")
plt.show()
