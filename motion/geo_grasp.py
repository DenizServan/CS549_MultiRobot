"""
A grasp found from geometry only, for pieces that cannot be read yet (in a pile): a straight piece of stroke on the
top of a blob, with room for the two fingers on both sides.

    getGeometricGrasp(view, C, camera, xy, floor_z)        ->  (grasp xy, closing angle, top height) or None
    getHeldPiece(C, names, templates, grasp_xy, closing, z) ->  name of the true piece the fingers would hold, or None

Idea: around a candidate point on the blob's top, the stroke points form a long thin cloud. Its principal direction
(PCA of the xy coordinates) is the stroke direction; the fingers close across it, at the middle of the stroke.
A finger place is blocked if any measured point there (of this piece or another) is higher than the fingertips.
"""
import os
import sys
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs
from ground_truth import getTruth


def getStroke(neighbours):
    """
    Returns (centre xy, stroke direction, stroke width, elongation) of the points around a candidate: PCA of their xy;
    the centre is the middle of the points across the stroke.
    """
    xy = neighbours[:, :2]
    m = xy.mean(axis=0)
    values, vectors = np.linalg.eigh(np.cov((xy - m).T))    # ascending eigenvalues
    along, across = vectors[:, 1], vectors[:, 0]
    s = (xy - m) @ across
    centre = m + across * (s.max() + s.min()) / 2
    return centre, along, s.max() - s.min(), np.sqrt(values[1] / max(values[0], 1e-12))


def getFingersFree(all_points, centre, along, width, z_grasp):
    """
    True if no measured point lies in the place of either finger (beside the stroke, FINGER_GAP away, FINGER_DEPTH
    thick, FINGER_WIDTH long) above the fingertips (z_grasp - FINGER_CLEARANCE).
    """
    across = np.array([-along[1], along[0]])
    d = all_points[:, :2] - centre
    a, c = d @ along, d @ across
    inner, outer = width / 2 + mp.FINGER_GAP, width / 2 + mp.FINGER_GAP + mp.FINGER_DEPTH
    in_finger = (np.abs(a) < mp.FINGER_WIDTH / 2) & (np.abs(c) > inner) & (np.abs(c) < outer)
    return not np.any(in_finger & (all_points[:, 2] > z_grasp - mp.FINGER_CLEARANCE))


def getGeometricGrasp(view, C, camera, xy, floor_z):
    """
    Looks with `camera` and returns a grasp on the blob nearest xy that has nothing lying on it: (grasp xy, closing
    angle, height of the top there), the straight stroke piece closest to the blob's centre with free finger places.
    None if there is no such grasp.
    """
    rgb, points, valid, size = takePicture(view, C, camera)
    blobs = [b for b in getBlobs(rgb, points, valid, size, getIgnoreBoxes(C, camera), floor_z) if not b["occluded"]]
    if not blobs:
        return None
    blob = min(blobs, key=lambda b: np.min(np.linalg.norm(b["points"][:, :2] - xy, axis=1)))
    P = blob["points"]
    if np.min(np.linalg.norm(P[:, :2] - xy, axis=1)) > .1:
        return None
    obstacles = points[valid]
    tree = cKDTree(P[:, :2])
    cells = np.unique(np.round(P[:, :2] / mp.GEO_CANDIDATE_STEP), axis=0) * mp.GEO_CANDIDATE_STEP
    middle = P[:, :2].mean(axis=0)
    best = None
    for c in cells:
        idx = tree.query_ball_point(c, mp.GEO_NEIGHBOUR_RADIUS)
        if len(idx) < mp.GEO_MIN_NEIGHBOURS:
            continue
        centre, along, width, elongation = getStroke(P[idx])
        if elongation < mp.GEO_MIN_ELONGATION or width > mp.GEO_MAX_STROKE_WIDTH:
            continue
        top = float(np.median(P[idx, 2]))
        z_grasp = top - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN
        if not getFingersFree(obstacles, centre, along, width, z_grasp):
            continue
        d = np.linalg.norm(centre - middle)
        if best is None or d < best[0]:
            best = (d, centre, np.arctan2(-along[0], along[1]), top)     # closing axis = across the stroke
    return None if best is None else best[1:]


def getHeldPiece(C, names, templates, grasp_xy, closing, z):
    """
    Ground truth (the fingers are not simulated): returns the name of the top-most true piece whose stroke the fingers
    would close on at (grasp_xy, gripper height z) along `closing`: the grasp point is on one of its strokes (within
    GEO_TOL_STROKE), the closing axis is across that stroke (GEO_TOL_ANGLE_DEG) and the
    height fits (GRASP_TOL_Z). None if no piece would be held.
    """
    hits = []
    for p in getTruth(C, names):
        k = templates["symbols"].index(p["symbol"])
        f = C.getFrame(p["name"])
        R, pos = f.getRotationMatrix(), f.getPosition()
        top_guess = z + mp.ORIGIN_BELOW_TOP - mp.GRASP_ABOVE_ORIGIN
        local = R.T @ (np.r_[grasp_xy, top_guess] - pos)
        pts = templates["points"][k]
        d = np.linalg.norm(pts - local[:2], axis=1)
        if d.min() > prm.TEMPLATE_SAMPLE_STEP + mp.GEO_TOL_STROKE:     # template points fill the strokes
            continue
        near = pts[d < mp.GEO_NEIGHBOUR_RADIUS + mp.STROKE_HALF_WIDTH]
        if len(near) < 3:
            continue
        _, along_local, _, _ = getStroke(np.c_[near, np.zeros(len(near))])
        along = (R[:2, :2] @ along_local)
        along /= np.linalg.norm(along)
        if abs(np.cos(closing) * along[0] + np.sin(closing) * along[1]) > np.sin(np.radians(mp.GEO_TOL_ANGLE_DEG)):
            continue                                        # not across the stroke
        top = (pos + R @ np.r_[local[:2], prm.PIECE_THICKNESS])[2]
        if abs(z - (top - mp.ORIGIN_BELOW_TOP + mp.GRASP_ABOVE_ORIGIN)) < mp.GRASP_TOL_Z:
            hits.append((top, p["name"]))
    return max(hits)[1] if hits else None
