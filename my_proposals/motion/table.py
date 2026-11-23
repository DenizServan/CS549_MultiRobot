"""
The table: its cells (where the letters go) and where the base stands to reach a cell.

    getCells(C, table)                      ->  list of cell centres xy in reading order
    getTableTop(C, table)                   ->  height of the table top
    getStandSpots(C, robot, table, xy)      ->  base poses (x, y, yaw) in front of xy, one per table side, nearest first
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import motion_parameters as mp
from scene_builder import getHalfExtentsWorld
from base import isFree, getBasePose


def getCells(C, table):
    """
    Returns the centres of the table's coloured squares in reading order for someone in front of the tables (looking
    +x): far row first (largest x), each row from the reader's left (+y). The centre square is left out if
    SKIP_CENTRE_CELL (no side of the table is close enough to reach it).
    """
    side = mp.TABLE_SIDE[table]
    xy = [C.getFrame(mp.CELL_FRAME_PATTERN.format(k=k, side=side)).getPosition()[:2] for k in range(1, 10)]
    xy = sorted(xy, key=lambda p: (-round(p[0], 2), -round(p[1], 2)))
    if mp.SKIP_CENTRE_CELL:
        centre = C.getFrame(table).getPosition()[:2]
        xy = [p for p in xy if np.linalg.norm(p - centre) > .05]
    return xy


def getTableTop(C, table):
    """
    Returns the height of the table's top face.
    """
    f = C.getFrame(table)
    return f.getPosition()[2] + getHalfExtentsWorld(f)[2]


def getStandSpots(C, robot, table, xy):
    """
    Returns base poses (x, y, yaw) for reaching the point xy on the table: for each table side, the point straight out
    from xy, TABLE_STANDOFF beyond the edge, facing xy. Only free spots, nearest to the base first.
    """
    f = C.getFrame(table)
    c, h = f.getPosition()[:2], getHalfExtentsWorld(f)[:2]
    spots = []
    for axis in (0, 1):
        for sign in (-1, 1):
            p = np.array(xy, float)
            p[axis] = c[axis] + sign * (h[axis] + mp.TABLE_STANDOFF)
            if isFree(C, robot, p):
                spots.append(np.r_[p, np.arctan2(xy[1] - p[1], xy[0] - p[0])])
    here = getBasePose(C, robot)[:2]
    return sorted(spots, key=lambda s: np.linalg.norm(s[:2] - here))
