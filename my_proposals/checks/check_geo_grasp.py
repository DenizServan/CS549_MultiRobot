"""
CHECK geo_grasp.py (spreading piles): where does the geometric grasp go, and would the fingers hold a piece there?

    python3 checks/check_geo_grasp.py                                  camera over the highest piece of the scene
    python3 checks/check_geo_grasp.py --x 1.2 --y 0.4

The free wrist-like camera looks down from WRIST_LOOKS[0] above the top at (x, y), as spread.py does, then
getGeometricGrasp() picks a grasp on the uncovered blob nearest (x, y) and getHeldPiece() asks the truth which piece
the fingers would hold. Plot: all points coloured by height, the chosen blob in black, the grasp point (star), the
closing axis (red line) and the two finger places (red boxes, approximate: stroke width from motion_parameters).

What correct looks like: the star sits in the middle of ONE straight stroke, the red line runs across that stroke,
the finger boxes are on empty floor or lower pieces (nothing higher inside them), and getHeldPiece names the TOP piece.
"""
import numpy as np
import matplotlib.pyplot as plt
from common import getArgs, makeScene, prm, loadTemplates
from evaluate import placeCamera
from camera import takePicture
import motion_parameters as mp
from geo_grasp import getGeometricGrasp, getHeldPiece

args = getArgs()
s = makeScene(args)
C, floor_z, truth, view, cam = s["C"], s["floor_z"], s["truth"], s["view"], prm.TEST_WRIST_CAMERA_NAME
templates = loadTemplates(cells=())
if args.x is None or args.y is None:
    top_piece = max(truth, key=lambda p: p["z"])
    xy, z_top = top_piece["xy"], top_piece["z"] + prm.PIECE_THICKNESS
    print(f"looking at the highest piece: {top_piece['name']}")
else:
    xy = np.array([args.x, args.y])
    z_top = min(truth, key=lambda p: np.linalg.norm(p["xy"] - xy))["z"] + prm.PIECE_THICKNESS
placeCamera(C, cam, xy, z_top + mp.WRIST_LOOKS[0][0], 0.)

grasp = getGeometricGrasp(view, C, cam, xy, floor_z)
_, points, valid, _ = takePicture(view, C, cam)
P = points[valid]
near = np.linalg.norm(P[:, :2] - xy, axis=1) < .3
fig, ax = plt.subplots(figsize=(9, 9))
sc = ax.scatter(P[near, 0], P[near, 1], c=100 * (P[near, 2] - floor_z), s=2, cmap="viridis")
plt.colorbar(sc, label="height above floor (cm)")
ax.plot(*xy, "k+", ms=15)
if grasp is None:
    print("no grasp found (no uncovered blob near xy, or no straight stroke with free finger places)")
else:
    g_xy, closing, top = grasp
    z = top - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN
    held = getHeldPiece(C, s["names"], templates, g_xy, closing, z)
    d = np.array([np.cos(closing), np.sin(closing)])          # closing axis
    along = np.array([-d[1], d[0]])
    print(f"grasp at ({g_xy[0]:.3f}, {g_xy[1]:.3f}), closing angle {np.degrees(closing):.0f}°, "
          f"top {100 * (top - floor_z):.1f} cm above floor -> fingers would hold: {held}")
    above = [p for p in truth if np.linalg.norm(p["xy"] - g_xy) < .15]
    print("true pieces within 15 cm (name, top height cm):",
          sorted([(p["name"], round(100 * (p["z"] + prm.PIECE_THICKNESS - floor_z), 1)) for p in above],
                 key=lambda t: -t[1]))
    ax.plot(*g_xy, "r*", ms=15)
    ax.plot(*np.c_[g_xy - .05 * d, g_xy + .05 * d], "r-")
    off = mp.STROKE_HALF_WIDTH + mp.FINGER_GAP + mp.FINGER_DEPTH / 2
    for sgn in (1, -1):
        c = g_xy + sgn * off * d
        corners = np.array([c + a * mp.FINGER_WIDTH / 2 * along + b * mp.FINGER_DEPTH / 2 * d
                            for a, b in ((1, 1), (1, -1), (-1, -1), (-1, 1), (1, 1))])
        ax.plot(corners[:, 0], corners[:, 1], "r-")
ax.set_aspect("equal")
ax.set_title("geometric grasp: star = grasp point, red = closing axis and finger places")
plt.show()
