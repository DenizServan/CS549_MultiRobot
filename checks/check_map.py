"""
CHECK piece_map.py and the decisions spell.py makes from it: after one robot scans the room with its mast camera,
what does the shared map believe, and which entries would a robot fetch, spread, inspect or ignore?

    python3 checks/check_map.py --reader cnn                 scan from every viewpoint (headless driving)
    python3 checks/check_map.py --reader cnn --views 6       only 6 viewpoints

p1 drives to the explore viewpoints (base.driveTo run on its own) and scans from each one (pick.scan = readPicture +
updateMap, which also forgets entries a new picture no longer shows). p2 stays home. Then each map entry is compared
with the truth:
    sure      conf >= CONF_ACT: findPiece fetches these first
    maybe     not sure, but not cut / covered: findPiece's second choice if it is the wanted letter
    pile      the top of a pile (spread.isInPile): spread when the letter is not found elsewhere
    ignored   cut or covered by another piece: nothing is done with it until something changes
    right     symbol matches the true piece under it (the pile's top piece if several)
Plot: truth in grey; entries coloured by category, red ring = wrong symbol, x = phantom (no true piece within 5 cm).

What to look for: wrong symbols among "sure" entries (the robot will fetch the wrong piece and only the wrist look can
save it); phantoms; two entries on one true piece (duplicates); true pieces with no entry (never seen).
"""
import numpy as np
import matplotlib.pyplot as plt
from common import getArgs, getClassifier, prm, loadTemplates, ry
from scene_builder import buildScene
from ground_truth import getTruth
import motion_parameters as mp
from arm import runToEnd
from base import driveTo, getBasePose, isFree
from piece_map import getViewpoints
from pick import scan, getTruePiece
from spread import isInPile

args = getArgs(lambda ap: ap.add_argument("--views", type=int, default=100, help="max viewpoints to scan from"))
C, names, floor_z, _ = buildScene(args.word, args.seed, verbose=True)
world = {"C": C, "view": ry.CameraView(C), "templates": loadTemplates(), "classifier": getClassifier(args.reader),
         "floor_z": floor_z, "names": names, "entries": []}
robot = mp.ROBOTS[0]
cam = prm.MAST_CAMERA_PATTERN.format(robot=robot)

scan(world, robot, cam)
viewpoints, n = getViewpoints(C), 1
while viewpoints and n < args.views:
    here = getBasePose(C, robot)[:2]
    v = viewpoints.pop(int(np.argmin([np.linalg.norm(p - here) for p in viewpoints])))
    if isFree(C, robot, v) and runToEnd(C, driveTo(C, robot, v, getBasePose(C, robot)[2]), show=False):
        scan(world, robot, cam)
        n += 1
entries = world["entries"]
print(f"\nscanned from {n} spots, {len(entries)} map entries, {len(names)} true pieces\n")

truth = getTruth(C, names)
hit, rows = {}, []
print(f"{'entry':>5s} {'read':>4s} {'true':>4s} {'conf':>6s} {'category':>8s} {'flags':20s}")
for i, e in enumerate(entries):
    r = e["read"]
    p = getTruePiece(r, truth)
    cat = "sure" if r["conf"] >= prm.CONF_ACT else "pile" if isInPile(C, e, robot) else \
        "maybe" if not (r["cut"] or r["occluded"]) else "ignored"
    right = p is not None and p["symbol"] == r["symbol"]
    if p is not None:
        hit.setdefault(p["name"], []).append(i)
    flags = ",".join(f for f in ("cut", "occluded", "stacked") if r[f])
    rows.append((r, p, cat, right))
    print(f"{i:5d} {r['symbol']:>4s} {p['symbol'] if p else '-':>4s} {r['conf']:6.3f} {cat:>8s} {flags:20s}"
          + ("" if right else "  WRONG" if p else "  PHANTOM"))

sure = [x for x in rows if x[2] == "sure"]
print(f"\nsure entries: {len(sure)}, wrong symbol among them: {sum(not x[3] for x in sure)}")
print(f"entries per category: { {c: sum(x[2] == c for x in rows) for c in ('sure', 'maybe', 'pile', 'ignored')} }")
print(f"phantoms: {sum(x[1] is None for x in rows)}, true pieces with 2+ entries: "
      f"{sum(len(v) > 1 for v in hit.values())}, true pieces never on the map: {len(truth) - len(hit)}")

colours = {"sure": "green", "maybe": "orange", "pile": "blue", "ignored": "gray"}
fig, ax = plt.subplots(figsize=(11, 11))
for p in truth:
    ax.plot(*p["xy"], "o", color="0.85", ms=12)
    ax.text(*p["xy"], p["symbol"], ha="center", va="center", fontsize=7, color="0.5")
for r, p, cat, right in rows:
    ax.plot(*r["xy"], "o" if p else "x", color=colours[cat], ms=6)
    if not right:
        ax.plot(*r["xy"], "o", mfc="none", mec="red", ms=12)
    ax.text(r["xy"][0] + .04, r["xy"][1] + .04, r["symbol"], color=colours[cat], fontsize=8)
for c, col in colours.items():
    ax.plot([], [], "o", color=col, label=c)
ax.plot([], [], "o", mfc="none", mec="red", label="wrong symbol")
ax.legend()
ax.set_aspect("equal")
ax.set_title("shared map after scanning (grey = truth)")
plt.show()
