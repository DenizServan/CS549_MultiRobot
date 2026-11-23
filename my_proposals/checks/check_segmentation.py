"""
CHECK steps 2-3 (camera.py, segmentation.py): does one picture become one blob per visible piece top?

    python3 checks/check_segmentation.py                         far view over a random piece, seed 0
    python3 checks/check_segmentation.py --pile --kind close
    python3 checks/check_segmentation.py --x -2.5 --y 2.5

Left: the camera's colour image. Middle: blobs in the image, one colour each, numbered (white outline = cut by the
image border / an ignore box, red outline = covered by another blob). Right: top view, blob points over the TRUE piece
strokes (grey) so you can see which piece each blob belongs to.

What correct looks like:
  - every piece top you can see in the colour image has exactly one blob (two touching pieces at the same height are
    ONE blob on purpose: the reader splits them later)
  - a piece lying on another one is a separate blob from the piece below, and the lower one is listed as covered
  - no blobs on the floor, the tables, the robot bases or the arm (those are removed by height band + ignore boxes)
  - blobs touching the image edge are marked cut
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation
from common import getArgs, makeScene, truePiecePoints, nearestTruth, prm, loadTemplates
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs, getPieceMask, getUpFacing

args = getArgs()
s = makeScene(args)
C, floor_z, truth = s["C"], s["floor_z"], s["truth"]
templates = loadTemplates(cells=())
rgb, points, valid, size = takePicture(s["view"], C, s["camera"])
boxes = getIgnoreBoxes(C)
blobs = getBlobs(rgb, points, valid, size, boxes, floor_z)

# how many pixels each filter removes (if blobs are missing, one of these removed them)
keep, hidden = getPieceMask(points, valid, boxes, floor_z)
up = getUpFacing(points, size)
print(f"\npixels: {valid.sum()} valid, {keep.sum()} in the piece height band outside ignore boxes, "
      f"{(keep & up).sum()} of those face up, {hidden.sum()} inside ignore boxes")
print(f"{len(blobs)} blobs\n")
print(f"{'blob':>4s} {'points':>6s} {'cut':>4s} {'covered_by':>10s} {'height above floor (cm)':>24s}  nearest true piece")
for i, b in enumerate(blobs):
    h = 100 * (b["points"][:, 2] - floor_z)
    p, d = nearestTruth(b["points"][:, :2].mean(axis=0), truth)
    print(f"{i:4d} {len(b['points']):6d} {str(b['cut']):>4s} {str(b['covered_by']):>10s} "
          f"{h.min():7.1f} .. {h.max():5.1f}         {p['symbol']} ({p['name']}, {100 * d:.0f} cm away)")

H, W = size
labels = np.zeros(H * W, int)
for i, b in enumerate(blobs):
    labels[b["pixels"]] = i + 1
labels = labels.reshape(H, W)

fig, ax = plt.subplots(1, 3, figsize=(18, 6))
ax[0].imshow(rgb.reshape(H, W, 3))
ax[0].set_title(f"camera image ({s['camera']})")
ax[1].imshow(np.ma.masked_equal(labels, 0), cmap="tab20", interpolation="nearest")
for i, b in enumerate(blobs):
    mask = labels == i + 1
    edge = binary_dilation(mask) & ~mask
    if b["cut"] or b["occluded"]:
        yy, xx = np.nonzero(edge)
        ax[1].plot(xx, yy, ",", color="red" if b["occluded"] else "black")
    r, c = np.unravel_index(b["pixels"], (H, W))
    ax[1].text(c.mean(), r.mean(), str(i), fontsize=9, ha="center", va="center")
ax[1].set_xlim(0, W)
ax[1].set_ylim(H, 0)
ax[1].set_title("blobs in the image (black edge = cut, red edge = covered)")
for p in truth:
    tp = truePiecePoints(p, templates)
    ax[2].plot(tp[:, 0], tp[:, 1], ".", color="0.85", ms=1)
for i, b in enumerate(blobs):
    ax[2].plot(b["points"][:, 0], b["points"][:, 1], ".", ms=1.5)
    m = b["points"][:, :2].mean(axis=0)
    ax[2].text(m[0], m[1], str(i), fontsize=9)
for centre, half in boxes:
    ax[2].add_patch(plt.Rectangle(centre - half, *(2 * half), fill=False, ls="--", color="gray"))
pts = np.vstack([b["points"][:, :2] for b in blobs]) if blobs else s["cam_xy"][None]
ax[2].set_xlim(pts[:, 0].min() - .3, pts[:, 0].max() + .3)
ax[2].set_ylim(pts[:, 1].min() - .3, pts[:, 1].max() + .3)
ax[2].set_aspect("equal")
ax[2].set_title("top view: blob points over true strokes (grey); dashed = ignore boxes")
plt.tight_layout()
plt.show()
