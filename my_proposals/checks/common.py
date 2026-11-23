"""
Shared setup for the check scripts: path setup, one scene, one camera placed where you ask.
Nothing here changes the pipeline; it only calls the functions in perception/ and motion/.
"""
import os
import sys
import argparse
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "perception"))
sys.path.insert(0, os.path.join(ROOT, "motion"))

import robotic as ry  # type: ignore
import parameters as prm
from scene_builder import buildScene
from evaluate import addWristTestCamera, placeCamera
from templates import loadTemplates, turnPoints
from ground_truth import getTruth


def getArgs(extra=None):
    """
    Common command line: --seed, --word, --kind far|close, --x --y (camera over this floor point; default:
    over a random piece; --pile: over a piece lying on another one), --heading (deg), --reader template|cnn.
    extra(ap) may add more arguments.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--word", default=prm.WORD, help="word of the task scene (its letters get spare copies)")
    ap.add_argument("--kind", choices=["far", "close"], default="far", help="far = mast-like camera, close = wrist-like")
    ap.add_argument("--x", type=float, default=None)
    ap.add_argument("--y", type=float, default=None)
    ap.add_argument("--heading", type=float, default=0., help="camera heading in degrees")
    ap.add_argument("--pile", action="store_true", help="camera over a random piece lying on another (a pile)")
    ap.add_argument("--reader", choices=["template", "cnn"], default="template")
    if extra:
        extra(ap)
    args = ap.parse_args()
    prm.CONF_ACT, prm.CONF_VERIFY, prm.CONF_ACCEPT = prm.READER_THRESHOLDS[args.reader]   # the robots' thresholds
    return args


def makeScene(args):
    """
    Builds the task scene and places the free test camera. Returns a dict with C, names, floor_z, view, truth, camera.
    Far: camera TEST_CAMERA_HEIGHT above the floor. Close: WRIST_VIEW_HEIGHT above the top of the piece below it
    (the same placements evaluate.py uses).
    """
    C, names, floor_z, _ = buildScene(args.word, seed=args.seed, cameras=("test",), verbose=True)
    addWristTestCamera(C)
    truth = getTruth(C, names)
    if args.x is None or args.y is None:
        pool = [p for p in truth if p["z"] > floor_z + 0.01] if args.pile else truth
        p = pool[np.random.default_rng(args.seed).integers(len(pool))]
        xy = p["xy"].copy()
        print(f"camera over piece {p['name']} at ({xy[0]:.2f}, {xy[1]:.2f}) (pass --x --y to choose)")
    else:
        xy = np.array([args.x, args.y])
    if args.kind == "far":
        cam, z = prm.TEST_CAMERA_NAME, floor_z + prm.TEST_CAMERA_HEIGHT
    else:
        below = min(truth, key=lambda p: np.linalg.norm(p["xy"] - xy))
        cam, z = prm.TEST_WRIST_CAMERA_NAME, below["z"] + prm.PIECE_THICKNESS + prm.WRIST_VIEW_HEIGHT
    placeCamera(C, cam, xy, z, np.radians(args.heading))
    return {"C": C, "names": names, "floor_z": floor_z, "view": ry.CameraView(C), "truth": truth, "camera": cam,
            "cam_xy": xy}


def getClassifier(name):
    if name == "cnn":
        from cnn.classify_cnn import CnnClassifier
        return CnnClassifier()
    from classify_template import classifyTemplate
    return classifyTemplate


def truePiecePoints(piece, templates):
    """
    Stroke points of a true piece at its true pose (room xy), for drawing the truth under the measurements.
    """
    return turnPoints(templates["points"][piece["k"]], piece["yaw"]) + piece["xy"]


def nearestTruth(xy, truth):
    """
    Returns (true piece nearest to xy, distance).
    """
    d = [np.linalg.norm(p["xy"] - xy) for p in truth]
    i = int(np.argmin(d))
    return truth[i], d[i]


def angleDiffDeg(a, b):
    return float(np.degrees(abs((a - b + np.pi) % (2 * np.pi) - np.pi)))
