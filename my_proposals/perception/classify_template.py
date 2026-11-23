"""
Classical reader: compares a blob's outline with all 36 letter templates at every rotation and small shift.

    classifyTemplate(description, templates)  ->  {"k", "yaw", "margin", "alts", "fit_check"}

        k          index of the winning symbol in SYMBOLS
        yaw        its coarse angle (multiple of COARSE_ANGLE_STEP_DEG)
        margin     confidence before refinement (relative margin, see confidence.py)
        alts       other symbols that scored almost as well
        fit_check  True: reader.py also applies confidence.fitPenalty (the fine fit must be good, not only the margin)

Score of symbol k at angle a and shift t (O = observed outline grid, T = template grid, H = hidden grid: cells covered
by pieces lying on this one, h = share of the observed black points that lie on the template's marks):
        S = |O ∩ T| / (|O| + |T| - u |T ∩ H| - |O ∩ T|) + DOT_WEIGHT * (2h - 1)
i.e. the overlap over the union, where template strokes that fall under a covering piece count only (1 - u) as
missing (u = UNSEEN_DISCOUNT; they cannot be seen, so they are weak evidence against the symbol). With nothing
hidden, or u = 0, this is the plain IoU.
The overlaps for all shifts and all symbols are counted at once by FFT cross-correlation.
"""
import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import binary_dilation
import parameters as prm
from templates import rasterize, rotatePoints
from confidence import templateMargin


def scoreAllShifts(O, D, strokes, marks, H=None):
    """
    Returns (scores, overlaps), each n_templates x (2s+1) x (2s+1): the score and the overlap |O ∩ T| of every
    template at every shift. O, D and H are the observed grids, larger than the templates by s cells on each side.
    """
    flip = (slice(None), slice(None, None, -1), slice(None, None, -1))      # correlation = convolution with a flip
    overlap = np.rint(fftconvolve(O[None], strokes[flip], mode="valid", axes=(1, 2)))
    union = O.sum() + strokes.sum(axis=(1, 2))[:, None, None] - overlap
    if prm.VISIBILITY_AWARE and H is not None and H.sum() > 0:             # strokes under a covering piece: unseen
        unseen = np.rint(fftconvolve(H[None], strokes[flip], mode="valid", axes=(1, 2)))
        union = np.maximum(union - prm.UNSEEN_DISCOUNT * unseen, overlap)
    iou = overlap / (union + 1e-9)
    if D.sum() == 0:                                                         # no black points seen: no mark term
        return iou, overlap
    hits = np.rint(fftconvolve(D[None], marks[flip], mode="valid", axes=(1, 2))) / D.sum()
    return iou + prm.DOT_WEIGHT * (2 * hits - 1), overlap


def getObservedGrids(desc, angle, cell, margin_cells):
    """
    Returns the outline, mark and hidden grids of a description, in a frame turned by `angle` about its centre.
    A hidden cell that also holds outline points counts as outline.
    """
    O = rasterize(rotatePoints(desc["top"] - desc["centre"], angle), cell, margin_cells).astype(float)
    D = rasterize(rotatePoints(desc["dark"] - desc["centre"], angle), cell, margin_cells).astype(float)
    hidden = desc.get("hidden", np.zeros((0, 2)))
    if len(hidden) == 0:
        return O, D, np.zeros_like(O)
    H = binary_dilation(rasterize(rotatePoints(hidden - desc["centre"], angle), cell, margin_cells))  # close pixel gaps
    return O, D, H.astype(float) * (1 - O)


def getScoreTable(desc, templates):
    """
    Returns scores[angle, symbol]: the best score of every symbol at every coarse angle (best over shifts).
    """
    strokes, marks = templates["grids"][prm.COARSE_GRID_CELL]
    table = np.zeros((prm.N_ANGLES, len(templates["symbols"])))
    for i, a in enumerate(prm.COARSE_ANGLES):
        O, D, H = getObservedGrids(desc, a, prm.COARSE_GRID_CELL, prm.SHIFT_CELLS)
        scores, _ = scoreAllShifts(O, D, strokes, marks, H)
        table[i] = scores.max(axis=(1, 2))
    return table


def classifyTemplate(desc, templates):
    """
    Returns the template reader's answer for one description (see the top of the file).
    """
    table = getScoreTable(desc, templates)
    ai, k = np.unravel_index(np.argmax(table), table.shape)
    best = table[ai, k]
    per_symbol = table.max(axis=0)
    alts = [templates["symbols"][j] for j in np.argsort(-per_symbol)[:4]
            if j != k and per_symbol[j] > prm.RUNNER_UP_RATIO * best]
    return {"k": int(k), "yaw": float(prm.COARSE_ANGLES[ai]), "alts": alts, "fit_check": True,
            "margin": templateMargin(table, k, ai, templates["sym180"][k])}
