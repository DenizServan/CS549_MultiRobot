"""
Evaluation: runs the reader on many camera views of task scenes it was not tuned on and compares with the truth.

    python3 perception/evaluate.py --reader cnn            the CNN reader on TEST_SEEDS (needs cnn/cnn_weights.pt)
    python3 perception/evaluate.py                         template reader
    python3 perception/evaluate.py --seeds 100-101 --far 4 --close 10      a quick run

Scenes: scene_builder.buildScene (the one task scene) with a random word per seed (getRandomWord).
Views: far views put the free mast-like test camera TEST_CAMERA_HEIGHT above random floor spots; close views put a
free wrist-like camera CLOSE_VIEW_HEIGHTS above random pieces, off-centre by CLOSE_VIEW_OFFSET_STD (like the robot's
wrist looks). Every view has a random heading.
Prints, per camera and per piece kind, how many reads are right, how many the robots would trust (with this reader's
READER_THRESHOLDS), and how many trusted reads are wrong; then the confidence thresholds that reach the target error
rates in parameters.py (run on CALIBRATION_SEEDS and copy them into READER_THRESHOLDS).
Piece kinds: whole (flat, open floor) / wall (flat, within WALL_NEAR of a wall) / stacked (flat, lying on another
piece) / tilted / cut (by the image border or an ignore box) / covered (by another piece) / none (matched no piece).
"""
import argparse
import numpy as np
import robotic as ry #type: ignore
import parameters as prm
from scene_builder import buildScene, addCamera, getCameraAttributes, getLookDownQuaternion, getRoomLimits
from templates import loadTemplates
from reader import readPicture
from classify_template import classifyTemplate
from ground_truth import getTruth, matchRead, isRight


# ------------------------------------------- 1. SCENES AND CAMERA VIEWS -----------------------------------------------------

def getRandomWord(seed):
    """
    Returns the random word of an evaluation / training scene: EVAL_WORD_LENGTH different symbols.
    """
    rng = np.random.default_rng(seed)
    return "".join(rng.choice(list(prm.SYMBOLS), size=prm.EVAL_WORD_LENGTH, replace=False))


def getPieceKind(read, piece, C, floor_z):
    """
    Returns the kind of piece a read belongs to (see the top of the file).
    """
    if piece is None:
        return "none"
    if read["cut"]:
        return "cut"
    if read["occluded"]:
        return "covered"
    if not piece["flat"]:
        return "tilted"
    if piece["z"] > floor_z + 0.01:
        return "stacked"
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    x, y = piece["xy"]
    return "wall" if min(x - x_min, x_max - x, y - y_min, y_max - y) < prm.WALL_NEAR else "whole"


def addWristTestCamera(C):
    """
    Adds a second free camera with wrist intrinsics (the scene builder's test camera has mast intrinsics).
    """
    return addCamera(C, prm.TEST_WRIST_CAMERA_NAME, None, [0., 0., 0.], prm.LOOK_DOWN_QUATERNION,
                     getCameraAttributes("wrist"))


def placeCamera(C, camera_name, xy, z, heading):
    """
    Puts a free camera at room position (x, y, z), looking straight down, turned by `heading`.
    """
    C.getFrame(camera_name).setPosition([xy[0], xy[1], z]).setQuaternion(getLookDownQuaternion(heading))


def getViews(C, truth, floor_z, seed, n_far, n_close):
    """
    Returns a list of views (kind, camera name, xy, z, heading): n_far far views over random floor spots and
    n_close close views over random pieces (choosing which piece to look at uses the ground truth, as a robot would
    have driven to a piece it saw).
    """
    rng = np.random.default_rng(seed + prm.VIEW_SEED_OFFSET)
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    views = []
    for _ in range(n_far):
        xy = rng.uniform([x_min, y_min], [x_max, y_max])
        views.append(("far", prm.TEST_CAMERA_NAME, xy, floor_z + prm.TEST_CAMERA_HEIGHT, rng.uniform(-np.pi, np.pi)))
    for i in rng.choice(len(truth), size=min(n_close, len(truth)), replace=False):
        p = truth[i]
        xy = p["xy"] + rng.normal(0., prm.CLOSE_VIEW_OFFSET_STD, 2)
        z = p["z"] + prm.PIECE_THICKNESS + rng.uniform(*prm.CLOSE_VIEW_HEIGHTS)
        views.append(("close", prm.TEST_WRIST_CAMERA_NAME, xy, z, rng.uniform(-np.pi, np.pi)))
    return views


# ------------------------------------------- 2. RUNNING THE READER ---------------------------------------------------------

def evaluateScene(seed, n_far, n_close, classifier, templates):
    """
    Returns one row per read in one task scene: kind (far/close), piece kind (getPieceKind), right, conf.
    """
    C, names, floor_z, _ = buildScene(getRandomWord(seed), seed=seed, cameras=("test",), verbose=False)
    addWristTestCamera(C)
    view = ry.CameraView(C)
    truth = getTruth(C, names)
    rows = []
    for kind, cam, xy, z, heading in getViews(C, truth, floor_z, seed, n_far, n_close):
        placeCamera(C, cam, xy, z, heading)
        for r in readPicture(view, C, cam, templates, floor_z, classifier):
            piece = matchRead(r, truth)
            piece_kind = getPieceKind(r, piece, C, floor_z)
            rows.append({"seed": seed, "kind": kind, "piece": piece_kind, "right": isRight(r, piece, templates),
                         "conf": r["conf"]})
    return rows


# ------------------------------------------- 3. SUMMARY AND THRESHOLDS -----------------------------------------------------

def getThreshold(rows, max_error):
    """
    Returns the lowest confidence c > 0 such that, among ALL reads with conf >= c, at most max_error are wrong.
    Reads with equal confidence are taken together (a threshold cannot keep one and drop the other).
    """
    confs = np.array([r["conf"] for r in rows])
    wrong = np.array([not r["right"] for r in rows])
    best = 1.
    for c in np.unique(confs[confs > 0])[::-1]:             # from the highest confidence down
        kept = confs >= c
        if wrong[kept].mean() > max_error:
            break
        best = c
    return best


def printSummary(rows):
    """
    Prints accuracy and trust per camera and piece kind, then the measured thresholds.
    """
    print(f"\n{'camera':6s} {'piece':7s} {'reads':>6s} {'right':>7s} {'trusted':>8s} {'trusted wrong':>14s}")
    for kind, limit in (("far", prm.CONF_ACT), ("close", prm.CONF_ACCEPT)):
        for piece in ("whole", "wall", "stacked", "tilted", "cut", "covered", "none"):
            r = [x for x in rows if x["kind"] == kind and x["piece"] == piece]
            if not r:
                continue
            trusted = [x for x in r if x["conf"] >= limit]
            wrong = np.mean([not x["right"] for x in trusted]) if trusted else 0.
            print(f"{kind:6s} {piece:7s} {len(r):6d} {100 * np.mean([x['right'] for x in r]):6.1f}% "
                  f"{100 * len(trusted) / len(r):7.1f}% {100 * wrong:13.1f}%")
    far = [x for x in rows if x["kind"] == "far"]
    close = [x for x in rows if x["kind"] == "close"]
    accept = getThreshold(close, prm.TARGET_ERROR_CLOSE) if close else float("nan")
    act = getThreshold(far, prm.TARGET_ERROR_FAR) if far else float("nan")
    print(f"\nmeasured thresholds: CONF_ACT = {act:.3f} (far, <= {100 * prm.TARGET_ERROR_FAR:.0f}% wrong), "
          f"CONF_ACCEPT = {accept:.3f} (close, <= {100 * prm.TARGET_ERROR_CLOSE:.0f}% wrong), "
          f"CONF_VERIFY ~ {accept / 2:.3f} (half of CONF_ACCEPT)")
    print("('none' = the read matched no true piece within MATCH_DISTANCE: always counted as wrong)")


def parseSeeds(text):
    """
    "100-109" -> [100, ..., 109];  "3" -> [3]
    """
    a, b = (text.split("-") + [text])[:2]
    return list(range(int(a), int(b) + 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", choices=["template", "cnn"], default="template")
    ap.add_argument("--seeds", default=f"{prm.TEST_SEEDS[0]}-{prm.TEST_SEEDS[-1]}")
    ap.add_argument("--far", type=int, default=prm.FAR_VIEWS_PER_SCENE)
    ap.add_argument("--close", type=int, default=prm.CLOSE_VIEWS_PER_SCENE)
    ap.add_argument("--trust-covered", action="store_true", help="measure as if DISTRUST_OCCLUDED were False")
    ap.add_argument("--no-visibility", action="store_true", help="measure as if VISIBILITY_AWARE were False")
    args = ap.parse_args()
    prm.CONF_ACT, prm.CONF_VERIFY, prm.CONF_ACCEPT = prm.READER_THRESHOLDS[args.reader]   # "trusted" as the robots
    prm.DISTRUST_OCCLUDED = prm.DISTRUST_OCCLUDED and not args.trust_covered
    prm.VISIBILITY_AWARE = prm.VISIBILITY_AWARE and not args.no_visibility

    templates = loadTemplates()
    if args.reader == "cnn":
        from cnn.classify_cnn import CnnClassifier
        classifier = CnnClassifier()
    else:
        classifier = classifyTemplate
    rows = []
    for seed in parseSeeds(args.seeds):
        rows += evaluateScene(seed, args.far, args.close, classifier, templates)
        print(f"seed {seed}: {len(rows)} reads so far", flush=True)
    printSummary(rows)
