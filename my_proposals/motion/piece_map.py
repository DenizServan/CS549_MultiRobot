"""
The robots' shared memory of the pieces they have seen: one entry per piece, built from all mast and wrist reads of
both robots.

    updateMap(entries, reads, C, camera)         merges new reads into the map, forgets pieces that are gone
    findPiece(C, entries, symbol, xy, robot)     ->  the nearest usable entry of a symbol, or None
    findUnreadable(C, entries, xy, robot)        ->  the nearest lone piece nobody could read yet, or None
    isReadable(read)                             ->  True if a closer look can give a trusted read (not cut/covered/tilted)
    removeNear(entries, xy)                      forgets the entry at xy (the piece was picked up)
    getViewpoints(C)                             ->  grid of floor points to scan the room from

entry = {"read": the best read so far, "tries": failed picks / looks, "ruled_out": symbols the wrist excluded,
         "alone": True once the piece was put down alone (spread.py), "claimed": robot working on it or None}
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from scene_builder import getRoomLimits, getFloorTop
from camera import getIgnoreBoxes
from clearance import isFarFromOthers


def getViewRadius(C, camera):
    """
    Returns (xy, radius) of a disc on the floor that a down-looking camera surely sees whatever its heading:
    FORGET_FRACTION of the shorter half side of its view.
    """
    pos = C.getFrame(camera).getPosition()
    height = pos[2] - getFloorTop(C)
    if "mast" in camera:
        half = prm.MAST_HEIGHT_PX / 2 / prm.MAST_FOCAL_PX
    else:
        half = prm.WRIST_HEIGHT_PX / 2 / prm.WRIST_FOCAL_PX
    return pos[:2], mp.FORGET_FRACTION * half * height


def updateMap(entries, reads, C=None, camera=None):
    """
    Merges reads into the map (a list of dicts). A read belongs to the NEAREST entry within MAP_MERGE_DISTANCE and
    replaces its read if it is at least as confident (a far mast read must not overwrite a sure wrist read); the entry
    keeps its history (tries, ruled_out, alone). Other reads become new entries.
    With C and camera: entries that this picture surely shows (getViewRadius, outside the ignore boxes) but that no
    read matched are forgotten: the piece was taken away or moved (entries someone is working on are kept).
    """
    matched = set()
    for r in reads:
        d = [np.linalg.norm(e["read"]["xy"] - r["xy"]) for e in entries]
        if d and min(d) < mp.MAP_MERGE_DISTANCE:
            e = entries[int(np.argmin(d))]
            if r["conf"] >= e["read"]["conf"]:
                e["read"] = r
            matched.add(id(e))
        else:
            entries.append({"read": r, "tries": 0, "ruled_out": set(), "alone": False, "claimed": None})
            matched.add(id(entries[-1]))
    if C is None:
        return
    centre, radius = getViewRadius(C, camera)
    boxes = getIgnoreBoxes(C, camera)
    seen = lambda xy: np.linalg.norm(xy - centre) < radius and \
        not any(np.all(np.abs(xy - c) < h) for c, h in boxes)
    entries[:] = [e for e in entries if id(e) in matched or e["claimed"] or not seen(e["read"]["xy"])]


def isUsable(C, e, robot):
    """
    True if an entry may be worked on by `robot`: fewer than MAX_TRIES_PER_PIECE failures, not claimed by the other
    robot, and not close to where the other robot works or stands (CLAIM_DISTANCE).
    """
    return e["tries"] < mp.MAX_TRIES_PER_PIECE and e["claimed"] in (None, robot) and \
        isFarFromOthers(C, robot, e["read"]["xy"])


def findPiece(C, entries, symbol, xy, robot):
    """
    Returns the usable entry of `symbol` nearest to xy that is worth going to, or None. First choice: reads with
    conf >= CONF_ACT. Second choice: low-confidence reads of the symbol that are fully visible (not cut, not covered,
    not tilted beyond MAX_TILT_DEG: those can only be read after spreading); e.g. the mast camera often cannot tell an
    S from an S turned upside down (only the small dots differ), but the wrist camera can. Entries the wrist camera
    ruled out for this symbol are skipped.
    """
    usable = [e for e in entries if e["read"]["symbol"] == symbol and symbol not in e["ruled_out"]
              and isUsable(C, e, robot)]
    sure = [e for e in usable if e["read"]["conf"] >= prm.CONF_ACT]
    maybe = [e for e in usable if isReadable(e["read"])]
    for group in (sure, maybe):
        if group:
            return min(group, key=lambda e: np.linalg.norm(e["read"]["xy"] - xy))
    return None


def isReadable(read):
    """
    True if a closer look can give a trusted read of this piece: it is not cut by the image border, not covered by
    another piece and not tilted beyond MAX_TILT_DEG.
    """
    return not (read["cut"] or read["occluded"] or read["tilt"] > np.radians(prm.MAX_TILT_DEG))


def findUnreadable(C, entries, xy, robot):
    """
    Returns the nearest usable entry of a piece lying alone on the floor (not stacked, isReadable) that no camera read
    confidently yet and nobody looked at closely (tries 0), or None. A wrist look decides what it is.
    """
    lone = [e for e in entries if e["read"]["conf"] < prm.CONF_ACT and e["tries"] == 0 and isUsable(C, e, robot)
            and not e["read"]["stacked"] and isReadable(e["read"])]
    return min(lone, key=lambda e: np.linalg.norm(e["read"]["xy"] - xy)) if lone else None


def removeNear(entries, xy):
    """
    Forgets the entries within MAP_MERGE_DISTANCE of xy (the piece there was picked up).
    """
    entries[:] = [e for e in entries if np.linalg.norm(e["read"]["xy"] - xy) >= mp.MAP_MERGE_DISTANCE]


def getViewpoints(C):
    """
    Returns a grid of floor points EXPLORE_SPACING apart covering the room: where the bases drive to scan.
    """
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    xs = np.arange(x_min + mp.EXPLORE_SPACING / 2, x_max, mp.EXPLORE_SPACING)
    ys = np.arange(y_min + mp.EXPLORE_SPACING / 2, y_max, mp.EXPLORE_SPACING)
    return [np.array([x, y]) for x in xs for y in ys]
