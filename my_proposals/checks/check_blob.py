"""
CHECK step 4 (blob.py): is each blob's top face found and laid flat correctly, and are the black marks found?

    python3 checks/check_blob.py --pile --kind close              (over a pile: tilted and stacked pieces)
    python3 checks/check_blob.py                                   far view, scattered room

One panel per blob (first 12): grey = raw blob points (x-y as seen), blue = top face laid flat, black = dark marks,
red x = hidden region (points of the pieces lying on this one). Printed per blob: points dropped by the plane fit,
measured tilt vs the true tilt of the nearest piece, stacked flag, number of dark points.

What correct looks like:
  - measured tilt is within a few degrees of the true tilt (flat pieces ~0)
  - blue looks like an undistorted letter; for a tilted piece it is LONGER than the grey (the squash is undone)
  - few points dropped by the plane fit (a few side-wall points); many dropped = the blob holds two surfaces
  - dark points sit on the glyph-bottom dots; 0 dark points on every blob = DARK_THRESHOLD does not match the render
  - stacked is True only for pieces lying on another piece
"""
import numpy as np
import matplotlib.pyplot as plt
from common import getArgs, makeScene, nearestTruth
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs
from blob import describeBlob, getTopFace

args = getArgs()
s = makeScene(args)
C, floor_z, truth = s["C"], s["floor_z"], s["truth"]
rgb, points, valid, size = takePicture(s["view"], C, s["camera"])
blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C), floor_z)

print(f"\n{'blob':>4s} {'pts':>5s} {'dropped':>7s} {'tilt':>6s} {'true tilt':>9s} {'stacked':>7s} {'dark':>5s} "
      f"{'cut':>5s} {'covered':>7s}  nearest true piece")
for i, b in enumerate(blobs):
    d = describeBlob(b, floor_z, blobs)
    on_face, _ = getTopFace(b["points"])
    p, dist = nearestTruth(d["centre"], truth)
    print(f"{i:4d} {len(b['points']):5d} {(~on_face).sum():7d} {np.degrees(d['tilt']):5.1f}° "
          f"{np.degrees(p['tilt']):8.1f}° {str(d['stacked']):>7s} {len(d['dark']):5d} {str(d['cut']):>5s} "
          f"{str(d['occluded']):>7s}  {p['symbol']} ({100 * dist:.0f} cm)")

n = min(len(blobs), 12)
if n == 0:
    raise SystemExit("no blobs in this view")
cols = 4
fig, axes = plt.subplots((n + cols - 1) // cols, cols, figsize=(16, 4 * ((n + cols - 1) // cols)), squeeze=False)
for i, ax in enumerate(axes.ravel()):
    if i >= n:
        ax.axis("off")
        continue
    b = blobs[i]
    d = describeBlob(b, floor_z, blobs)
    ax.plot(b["points"][:, 0], b["points"][:, 1], ".", color="0.75", ms=2, label="raw")
    ax.plot(d["top"][:, 0], d["top"][:, 1], ".", color="tab:blue", ms=1.5, label="laid flat")
    if len(d["dark"]):
        ax.plot(d["dark"][:, 0], d["dark"][:, 1], "k.", ms=3, label="dark")
    if len(d["hidden"]):
        ax.plot(d["hidden"][:, 0], d["hidden"][:, 1], "rx", ms=2, label="hidden")
    c = d["centre"]
    ax.set_xlim(c[0] - .2, c[0] + .2)
    ax.set_ylim(c[1] - .2, c[1] + .2)
    ax.set_aspect("equal")
    ax.set_title(f"blob {i}: tilt {np.degrees(d['tilt']):.0f}°" + (" stacked" if d["stacked"] else "")
                 + (" cut" if d["cut"] else "") + (" covered" if d["occluded"] else ""), fontsize=9)
axes[0, 0].legend(fontsize=7)
plt.tight_layout()
plt.show()
