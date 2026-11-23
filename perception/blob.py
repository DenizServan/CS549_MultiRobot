"""
Blob description: turns one surface from segmentation.py into the flat description the readers work with.

    describeBlob(blob, floor_z, blobs)  ->  description

The surface's top face is found by fitting a plane to its points; the points are then turned so that the plane is
horizontal and the height is dropped. A flat piece is unchanged; a piece lying tilted on another one is "laid flat",
so its outline is no longer squashed and the same templates / CNN can read it.

The description is a dict:
    "top"       K x 2 outline points of the top face, laid flat (room x-y for a flat piece)
    "dark"      J x 2 black top-face points (the glyph-bottom marks), laid flat the same way
    "hidden"    H x 2 points of the pieces lying on this one, laid flat the same way: where its outline may go on unseen
    "centre"    x-y mean of "top"
    "z_top"     height of the highest point (room z)
    "tilt"      angle between the top face and the floor (radians)
    "stacked"   True if the top face is higher than one piece: the piece lies on another one
    "cut"       True if it touches the image border
    "occluded"  True if another piece lies on it (part of its outline is hidden)
    "underside" True if more than MAX_DARK_SHARE of its points are black: a piece's black base layer, not a top face
"""
import numpy as np
import parameters as prm


def getPlaneNormal(pts):
    """
    Returns the unit normal (pointing up) of the plane that best fits the points: the direction of least spread,
    i.e. the singular vector of the centred points with the smallest singular value.
    """
    _, _, Vt = np.linalg.svd(pts - pts.mean(axis=0), full_matrices=False)
    n = Vt[-1]
    return n if n[2] > 0 else -n


def getTopFace(pts):
    """
    Returns (mask of the points on the top face, its normal). The plane is fitted twice: once to all points, then
    only to the points within PLANE_INLIER_TOLERANCE of it (side-wall points the segmentation kept are dropped).
    """
    n = getPlaneNormal(pts)
    on_face = np.abs((pts - pts.mean(axis=0)) @ n) < prm.PLANE_INLIER_TOLERANCE
    if on_face.sum() >= 3:
        n = getPlaneNormal(pts[on_face])
        on_face = np.abs((pts - pts[on_face].mean(axis=0)) @ n) < prm.PLANE_INLIER_TOLERANCE
    return on_face, n


def getFlatteningRotation(n):
    """
    Returns the smallest rotation that turns the unit normal n into the vertical (0, 0, 1) (Rodrigues' formula).
    Turning about the horizontal axis n x z keeps the piece's heading, so the angle read after laying it flat is
    its heading in the room.
    """
    z = np.array([0., 0., 1.])
    v = np.cross(n, z)
    s, c = np.linalg.norm(v), n @ z
    if s < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)


def describeBlob(blob, floor_z, blobs=None):
    """
    Returns the description of one surface (see the top of the file). blobs: all blobs of the picture; the points of
    the blobs that cover this one become "hidden" (laid flat the same way): there the piece may go on unseen.
    """
    pts, rgb = blob["points"], blob["rgb"]
    on_face, n = getTopFace(pts)
    face, face_rgb = pts[on_face], rgb[on_face]
    centre3 = face.mean(axis=0)
    flat = (face - centre3) @ getFlatteningRotation(n).T + centre3      # laid flat about its own centre
    dark = face_rgb.max(axis=1) < prm.DARK_THRESHOLD                    # black in all three colour channels
    top = flat[:, :2]
    z_top = pts[:, 2].max()
    R = getFlatteningRotation(n)
    covering = [blobs[i]["points"] for i in blob.get("covered_by", [])] if blobs is not None else []
    hidden = ((np.vstack(covering) - centre3) @ R.T + centre3)[:, :2] if covering else np.zeros((0, 2))
    return {"top": top, "dark": flat[dark, :2], "hidden": hidden, "centre": top.mean(axis=0), "z_top": float(z_top),
            "tilt": float(np.arccos(np.clip(n[2], -1., 1.))), "stacked": bool(z_top - floor_z > prm.STACKED_HEIGHT),
            "cut": blob["cut"], "occluded": blob["occluded"], "underside": bool(dark.mean() > prm.MAX_DARK_SHARE)}


def subDescription(desc, keep_top, keep_dark):
    """
    Returns a copy of a description with only some of its points (used to split blobs of touching pieces).
    """
    top = desc["top"][keep_top]
    return {**desc, "top": top, "dark": desc["dark"][keep_dark], "centre": top.mean(axis=0)}
