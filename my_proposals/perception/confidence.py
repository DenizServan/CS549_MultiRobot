"""
Confidence: how much a read can be trusted, as one number (0 = no idea, higher = surer).

    templateMargin(scores, k, angle_index, sym180)   relative margin of the best template hypothesis
    coveragePenalty(precision)                       lowers confidence when the blob holds more than one piece
    fitPenalty(fit_score, points_per_cell)           lowers a read whose template fits badly (fragments, cut-off pieces)
    calibrate(margin, calibration)                   maps a CNN margin onto the template confidence scale
Thresholds that use the result (CONF_ACT, CONF_VERIFY, CONF_ACCEPT) are in parameters.py; evaluate.py measures them.
"""
import numpy as np
import parameters as prm


def wrapAngle(a):
    """
    Returns the angle mapped into [-pi, pi).
    """
    return (a + np.pi) % (2 * np.pi) - np.pi


def templateMargin(scores, k, angle_index, sym180):
    """
    Returns (best - best different answer) / best for the template score table scores[angle, symbol].
    A hypothesis is a different answer if it is another symbol, or the same symbol turned by more than
    DIFFERENT_ANGLE_DEG (a half turn does not count as different for glyphs that look the same that way).
    """
    best = scores[angle_index, k]
    d = np.abs(wrapAngle(prm.COARSE_ANGLES - prm.COARSE_ANGLES[angle_index]))        # angle difference of every row
    tol = np.radians(prm.DIFFERENT_ANGLE_DEG)
    same_look = d < tol                                                              # (nearly) the same angle
    if sym180:
        same_look |= np.abs(d - np.pi) < tol                                         # or a half turn of a symmetric glyph
    different = np.ones_like(scores, bool)
    different[same_look, k] = False                                                  # same symbol, same look
    competitor = scores[different].max()
    return float(np.clip((best - competitor) / max(best, 1e-6), 0., 1.))


def coveragePenalty(precision):
    """
    Returns a factor in [0, 1]: 1 if the fitted template explains at least COVERAGE_THRESHOLD of the blob,
    falling linearly to 0 at COVERAGE_FLOOR (the rest of the blob is probably another piece).
    """
    if precision >= prm.COVERAGE_THRESHOLD:
        return 1.
    return float(max(0., (precision - prm.COVERAGE_FLOOR) / (prm.COVERAGE_THRESHOLD - prm.COVERAGE_FLOOR)))


def fitPenalty(fit_score, points_per_cell):
    """
    Returns a factor in [0, 1] from the fine template fit of the answer (both readers): 0 below the low end of the ramp,
    1 above the high end. The ramp depends on point density (far views are sparse, close-ups dense).
    """
    lo, hi = prm.FIT_DENSE if points_per_cell >= prm.DENSE_POINTS_PER_CELL else prm.FIT_SPARSE
    return float(np.clip((fit_score - lo) / (hi - lo), 0., 1.))


def calibrate(margin, calibration):
    """
    Returns the CNN margin mapped piecewise-linearly onto the template confidence scale (calibration from train.py).
    """
    return float(np.interp(margin, calibration["margin"], calibration["conf"]))
