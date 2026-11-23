"""
Ground truth: the true symbol and pose of every piece. For EVALUATION and TRAINING DATA only; the reader never uses it.

    getTruth(C, piece_names)                 ->  list of true pieces {"name", "symbol", "k", "xy", "yaw", "tilt", "flat"}
    matchRead(read, truth)                   ->  the true piece a read belongs to (or None)
    isRight(read, piece, templates)          ->  symbol right and angle within ANGLE_TOLERANCE_DEG
    labelDescription(desc, truth, templates, label_covered) ->  (k, yaw) of the one piece that explains a blob, or (-1, nan)
"""
import numpy as np
import parameters as prm
from confidence import wrapAngle
from refine import explainedMask


def getSymbolOfPiece(name):
    """
    Returns the symbol of a piece from its frame name: the text after CHARACTER_FRAME_PREFIX ("c2_char_K" -> "K").
    """
    return name.split(prm.CHARACTER_FRAME_PREFIX)[1]


def getTruth(C, piece_names):
    """
    Returns the true pieces: name, symbol, symbol index, xy of the point on the top face above the piece origin (the
    same as the origin for a flat piece; what the reader estimates for a tilted one), yaw, tilt and whether it is flat.
    """
    truth = []
    for n in piece_names:
        f = C.getFrame(n)
        R = f.getRotationMatrix()
        s = getSymbolOfPiece(n)
        tilt = float(np.arccos(np.clip(abs(R[2, 2]), -1., 1.)))
        top_origin = f.getPosition() + R[:, 2] * prm.PIECE_THICKNESS
        truth.append({"name": n, "symbol": s, "k": prm.SYMBOLS.index(s), "xy": top_origin[:2],
                      "z": f.getPosition()[2], "yaw": float(np.arctan2(R[1, 0], R[0, 0])), "tilt": tilt,
                      "flat": bool(tilt < np.radians(prm.FLAT_TILT_DEG))})
    return truth


def matchRead(read, truth):
    """
    Returns the true piece whose origin is closest to the read's origin, if within MATCH_DISTANCE, else None.
    """
    d = [np.linalg.norm(p["xy"] - read["xy"]) for p in truth]
    i = int(np.argmin(d))
    return truth[i] if d[i] < prm.MATCH_DISTANCE else None


def isRight(read, piece, templates):
    """
    Returns True if the read names the right symbol at the right angle (a half turn is fine for symmetric glyphs).
    """
    if piece is None or read["k"] != piece["k"]:
        return False
    d = abs(wrapAngle(read["yaw"] - piece["yaw"]))
    tol = np.radians(prm.ANGLE_TOLERANCE_DEG)
    return bool(d < tol or (templates["sym180"][piece["k"]] and abs(d - np.pi) < tol))


def labelDescription(desc, truth, templates, label_covered=False):
    """
    Returns (k, yaw) of the true piece that explains at least LABEL_EXPLAINED_SHARE of the blob's (laid flat)
    outline, or (-1, nan) when no single piece does (touching pieces), when the blob is cut by the image border or
    covered by another piece (unless label_covered: CNN training data), when the piece is tilted more than
    LABEL_MAX_TILT_DEG, or when the blob shows less than LABEL_MIN_VISIBLE of the piece's strokes (a fragment: one
    stroke of a half-hidden piece cannot tell the symbol).
    """
    if desc["cut"] or (desc["occluded"] and not label_covered):
        return -1, float("nan")
    best_share, best = 0., None
    for p in truth:
        if np.linalg.norm(p["xy"] - desc["centre"]) > prm.TEMPLATE_HALF_Y + prm.MATCH_DISTANCE:
            continue
        share = explainedMask(desc["top"], templates, p["k"], p["yaw"], p["xy"], prm.LABEL_TOLERANCE).mean()
        if share > best_share:
            best_share, best = share, p
    if best is None or best_share < prm.LABEL_EXPLAINED_SHARE or best["tilt"] > np.radians(prm.LABEL_MAX_TILT_DEG):
        return -1, float("nan")
    if getVisibleShare(desc, best, templates) < prm.LABEL_MIN_VISIBLE:
        return -1, float("nan")                             # too little of the piece is visible to tell it
    return best["k"], best["yaw"]


def getVisibleShare(desc, piece, templates):
    """
    Returns the share of a true piece's stroke points (templates, placed at its pose) that have an outline point of
    the blob within LABEL_TOLERANCE: how much of the piece the camera sees.
    """
    from scipy.spatial import cKDTree
    pts = templates["points"][piece["k"]]
    c, s = np.cos(piece["yaw"]), np.sin(piece["yaw"])
    world = pts @ np.array([[c, s], [-s, c]]) + piece["xy"]
    dist, _ = cKDTree(desc["top"]).query(world[::4])          # every 4th model point is enough
    return float((dist < prm.LABEL_TOLERANCE).mean())
