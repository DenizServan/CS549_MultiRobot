"""
Refinement: the exact pose of a recognised piece and two checks on how well it fits.

    fineFit(description, templates, k, yaw)  ->  {"yaw", "xy", "score", "precision"}

        yaw        refined angle (FINE_ANGLE_STEP_DEG steps around the coarse one)
        xy         position of the piece ORIGIN in the room (the frame the grasp marker is defined in)
        score      template score at the refined pose (how well it fits)
        precision  share of the blob's outline cells the template covers (below COVERAGE_THRESHOLD: touching pieces)

    explainedMask(xy_points, templates, k, yaw, origin)  ->  which points lie on the strokes of that fitted piece
"""
import numpy as np
from scipy.spatial import cKDTree
import parameters as prm
from templates import turnPoints, rotatePoints
from classify_template import getObservedGrids, scoreAllShifts


def fineFit(desc, templates, k, yaw):
    """
    Returns the refined pose and fit of symbol k near angle yaw (see the top of the file).
    """
    strokes, marks = templates["grids"][prm.FINE_GRID_CELL]
    s, cell = prm.FINE_SHIFT_CELLS, prm.FINE_GRID_CELL
    best = None
    for da in prm.FINE_ANGLES:
        a = yaw + da
        O, D, H = getObservedGrids(desc, a, cell, s)
        scores, overlap = scoreAllShifts(O, D, strokes[k:k + 1], marks[k:k + 1], H)
        dy, dx = np.unravel_index(np.argmax(scores[0]), scores[0].shape)
        if best is None or scores[0, dy, dx] > best[0]:
            best = (scores[0, dy, dx], a, dx, dy, overlap[0, dy, dx] / max(O.sum(), 1.))
    score, a, dx, dy, precision = best
    # the template's centroid sits at (dx - s, dy - s) cells from the blob centre, in the frame turned by a
    centroid = desc["centre"] + turnPoints(np.array([[(dx - s) * cell, (dy - s) * cell]]), a)[0]
    origin = centroid - turnPoints(templates["centroid"][k][None], a)[0]
    return {"yaw": float(a), "xy": origin, "score": float(score), "precision": float(precision)}


def explainedMask(xy, templates, k, yaw, origin, tolerance=prm.EXPLAINED_TOLERANCE):
    """
    Returns a boolean per point: True if the point lies within `tolerance` of a stroke of symbol k placed at
    (origin, yaw). Used to split blobs of touching pieces and to label training data.
    """
    if len(xy) == 0:
        return np.zeros(0, bool)
    local = rotatePoints(xy - origin, yaw)                       # points in the piece frame
    dist, _ = cKDTree(templates["points"][k]).query(local)
    return dist < tolerance
