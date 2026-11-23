"""
CHECK steps 5-8 (classify_template.py or cnn/classify_cnn.py, refine.py, confidence.py) on ONE blob:
why did the reader pick this symbol and angle, and where does the confidence number come from?

    python3 checks/check_classify.py --blob 0                    blob numbers as printed by check_segmentation.py
    python3 checks/check_classify.py --blob 3 --reader cnn --pile --kind close

Template reader: heat map of the score table (angle x symbol): one bright spot = sure; two bright spots in one column
= the angle is ambiguous (e.g. S vs S turned 180°); bright spots in two columns = two symbols look alike.
CNN reader: the three input layers, the top symbol probabilities, the angle distribution.
Both: the blob outline (blue) with the chosen template at the refined pose (green) and the TRUE piece (red).

What correct looks like:
  - green lies on blue; red lies on green (red off green = wrong pose: the grasp will miss)
  - confidence breakdown: margin x coverage penalty (x fit penalty for the CNN), then 0 if cut / covered / too tilted
  - precision below COVERAGE_THRESHOLD (0.85) means the blob holds more than this piece: the reader splits it
"""
import numpy as np
import matplotlib.pyplot as plt
from common import getArgs, makeScene, getClassifier, truePiecePoints, nearestTruth, angleDiffDeg, prm, loadTemplates
from templates import turnPoints
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs
from blob import describeBlob
from classify_template import getScoreTable
from refine import fineFit
from confidence import coveragePenalty, fitPenalty
from reader import readDescription, isUntrusted, getPointsPerCell

args = getArgs(lambda ap: ap.add_argument("--blob", type=int, default=0))
s = makeScene(args)
C, floor_z, truth = s["C"], s["floor_z"], s["truth"]
templates = loadTemplates()
classifier = getClassifier(args.reader)
rgb, points, valid, size = takePicture(s["view"], C, s["camera"])
blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C), floor_z)
if args.blob >= len(blobs):
    raise SystemExit(f"only {len(blobs)} blobs in this view")
desc = describeBlob(blobs[args.blob], floor_z, blobs)

c = classifier(desc, templates)
fit = fineFit(desc, templates, c["k"], c["yaw"])
cov = coveragePenalty(fit["precision"])
fp = fitPenalty(fit["score"], getPointsPerCell(desc["top"])) if c["fit_check"] else 1.
sym = templates["symbols"][c["k"]]
p, dist = nearestTruth(fit["xy"], truth)

print(f"\nblob {args.blob}: {len(desc['top'])} outline points, {len(desc['dark'])} dark, {len(desc['hidden'])} hidden, "
      f"tilt {np.degrees(desc['tilt']):.1f}°, cut {desc['cut']}, covered {desc['occluded']}, stacked {desc['stacked']}")
print(f"reader ({args.reader}): '{sym}' coarse yaw {np.degrees(c['yaw']):.0f}°, alternatives {c['alts']}")
print(f"refined: yaw {np.degrees(fit['yaw']):.1f}°, origin ({fit['xy'][0]:.3f}, {fit['xy'][1]:.3f}), "
      f"fit score {fit['score']:.3f}, precision {fit['precision']:.2f}")
print(f"confidence = margin {c['margin']:.3f} x coverage penalty {cov:.2f} x fit penalty {fp:.2f} "
      f"= {c['margin'] * cov * fp:.3f}" + ("  -> set to 0 (cut / covered / too tilted)" if isUntrusted(desc) else ""))
print(f"thresholds: CONF_ACT {prm.CONF_ACT}, CONF_VERIFY {prm.CONF_VERIFY}, CONF_ACCEPT {prm.CONF_ACCEPT}")
print(f"truth: nearest piece '{p['symbol']}' ({p['name']}), origin error {100 * dist:.1f} cm, "
      f"yaw error {angleDiffDeg(fit['yaw'], p['yaw']):.1f}°"
      + ("  (half turn is fine: symmetric glyph)" if templates["sym180"][p["k"]] else ""))
print("what readPicture returns for this blob (after any split):")
for r in readDescription(desc, templates, classifier):
    print(f"   '{r['symbol']}' yaw {np.degrees(r['yaw']):6.1f}°  xy ({r['xy'][0]:.3f}, {r['xy'][1]:.3f})  "
          f"conf {r['conf']:.3f}  precision {r['precision']:.2f}")

fig = plt.figure(figsize=(16, 6))
ax = fig.add_subplot(1, 3, 1)
ax.plot(desc["top"][:, 0], desc["top"][:, 1], ".", color="tab:blue", ms=2, label="blob (laid flat)")
if len(desc["dark"]):
    ax.plot(desc["dark"][:, 0], desc["dark"][:, 1], "k.", ms=3, label="dark")
g = turnPoints(templates["points"][c["k"]], fit["yaw"]) + fit["xy"]
ax.plot(g[::3, 0], g[::3, 1], ".", color="tab:green", ms=1, alpha=.5, label=f"read '{sym}'")
tp = truePiecePoints(p, templates)
ax.plot(tp[::6, 0], tp[::6, 1], ".", color="tab:red", ms=1, alpha=.5, label=f"truth '{p['symbol']}'")
ax.plot(*fit["xy"], "g+", ms=12)
ax.plot(*p["xy"], "r+", ms=12)
m = desc["centre"]
ax.set_xlim(m[0] - .22, m[0] + .22)
ax.set_ylim(m[1] - .22, m[1] + .22)
ax.set_aspect("equal")
ax.legend(fontsize=7)
ax.set_title("+ = piece origin (green read, red truth)")

if args.reader == "template":
    table = getScoreTable(desc, templates)
    ax = fig.add_subplot(1, 3, (2, 3))
    im = ax.imshow(table, aspect="auto", cmap="viridis", origin="lower",
                   extent=[-.5, len(templates["symbols"]) - .5, 0, 360])
    ax.set_xticks(range(len(templates["symbols"])))
    ax.set_xticklabels(templates["symbols"])
    ax.set_ylabel("angle (deg)")
    ax.set_title(f"template score table (best over shifts); margin {c['margin']:.3f}")
    plt.colorbar(im, ax=ax)
else:
    import torch
    from model import getInputImage
    img = getInputImage(desc["top"] - desc["centre"], desc["dark"] - desc["centre"], desc["hidden"] - desc["centre"])
    with torch.no_grad():
        ls, la = classifier.net(torch.from_numpy(img[None, :classifier.n_layers]))
    ps, pa = torch.softmax(ls, 1).numpy()[0], torch.softmax(la, 1).numpy()[0]
    ax = fig.add_subplot(2, 3, 2)
    ax.imshow(np.dstack([img[0], img[1], img[2]]), origin="lower")
    ax.set_title("CNN input: red outline, green marks, blue hidden", fontsize=9)
    ax = fig.add_subplot(2, 3, 3)
    top5 = np.argsort(-ps)[:5]
    ax.bar([templates["symbols"][j] for j in top5], ps[top5])
    ax.set_title(f"symbol probabilities; calibrated margin {c['margin']:.3f}", fontsize=9)
    ax = fig.add_subplot(2, 3, (5, 6))
    ax.plot(np.arange(len(pa)) * 360 / len(pa), pa)
    ax.axvline(np.degrees(p["yaw"]) % 360, color="r", ls="--", label="true yaw")
    ax.set_xlabel("angle (deg)")
    ax.legend()
    ax.set_title("angle probabilities (a second peak 180° away = upside-down doubt)", fontsize=9)
plt.tight_layout()
plt.show()
