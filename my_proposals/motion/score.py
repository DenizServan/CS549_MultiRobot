"""
Scoring the spelled word with the ground truth (only here and in pick.fingersHold is the truth used).

    scoreTable(C, names, cells, letters, templates)   ->  one row per cell: what lies there and how well
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import motion_parameters as mp
from ground_truth import getTruth
from confidence import wrapAngle


def getCentre(C, piece, templates):
    """
    Returns the xy of a true piece's stroke centroid (its centre) in the room.
    """
    k = templates["symbols"].index(piece["symbol"])
    f = C.getFrame(piece["name"])
    return (f.getPosition() + f.getRotationMatrix() @ np.r_[templates["centroid"][k], 0.])[:2]


def scoreTable(C, names, cells, letters, templates):
    """
    For each cell: the true piece whose centre is nearest (within CELL_MATCH_DISTANCE), its symbol, its yaw error from
    UPRIGHT_YAW (a half turn is fine for a glyph that looks the same upside down) and its distance from the cell
    centre. A cell is correct if the symbol is right, the yaw error < YAW_OK_DEG and the distance < POSITION_OK.
    """
    truth = getTruth(C, names)
    centres = {p["name"]: getCentre(C, p, templates) for p in truth}
    rows = []
    for cell, letter in zip(cells, letters):
        near = [p for p in truth if np.linalg.norm(centres[p["name"]] - cell) < mp.CELL_MATCH_DISTANCE]
        if not near:
            rows.append({"want": letter, "got": "-", "ok": False})
            continue
        p = min(near, key=lambda p: np.linalg.norm(centres[p["name"]] - cell))
        d = abs(wrapAngle(p["yaw"] - mp.UPRIGHT_YAW))
        if templates["sym180"][p["k"]]:
            d = min(d, np.pi - d)
        yaw_err, pos_err = float(np.degrees(d)), float(np.linalg.norm(centres[p["name"]] - cell))
        rows.append({"want": letter, "got": p["symbol"], "yaw_err": yaw_err, "pos_err": pos_err,
                     "ok": p["symbol"] == letter and yaw_err < mp.YAW_OK_DEG and pos_err < mp.POSITION_OK})
    return rows
