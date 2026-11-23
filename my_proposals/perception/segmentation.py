"""
Segmentation: cuts the point cloud of one picture into blobs, one per visible SURFACE.

    getBlobs(rgb, points, valid, image_size, ignore_boxes, floor_z)  ->  list of blobs

Neighbouring pixels belong to the same surface only if their heights differ by less than SEG_DEPTH_JUMP. A piece lying
on another one is ~4 cm higher at its edge, so the two become separate blobs (grouping them by floor position, as
before, merged them). A tilted piece stays one blob: its height changes only by millimetres from pixel to pixel.
Steep pixels (side walls of pieces, seen at an angle by the mast camera) are dropped first: on a wall the height
changes only a little from pixel to pixel, so without this a wall would join the top of a piece to the piece below.
A blob that borders a HIGHER blob in the image is partly hidden under it: it is marked "occluded" and lists the blobs
that cover it.

Each blob is a dict:
    "points"      M x 3 room coordinates of its points
    "rgb"         M x 3 their colours
    "pixels"      M pixel indices into the flattened image (row i of the picture = pixel i)
    "cut"         True if it touches the image border or an ignore box (the piece may be only partly in view)
    "occluded"    True if another blob lies on it (its outline is incomplete)
    "covered_by"  indices (in the returned list) of the blobs lying on it
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import binary_dilation
import parameters as prm


def getPieceMask(points, valid, ignore_boxes, floor_z):
    """
    Returns (keep, hidden), N booleans each. keep: points that can belong to a piece, i.e. valid points between
    SEG_MIN_HEIGHT and SEG_MAX_HEIGHT above the floor, outside every ignore box (tables, robot bases). hidden: points
    in that height band but inside an ignore box (a piece next to a box may continue into it).
    """
    h = points[:, 2] - floor_z
    in_band = valid & (h > prm.SEG_MIN_HEIGHT) & (h < prm.SEG_MAX_HEIGHT)
    in_box = np.zeros(len(points), bool)
    for centre, half in ignore_boxes:
        in_box |= np.all(np.abs(points[:, :2] - centre) < half, axis=1)
    return in_band & ~in_box, in_band & in_box


def getUpFacing(points, image_size):
    """
    Returns N booleans: True where the surface faces up, i.e. its normal is within SEG_MAX_SLOPE_DEG of vertical.
    The normal is the cross product of the steps to the next pixel along a row and along a column; of the two
    neighbours (before / after) the one with the smaller height change is used, so a pixel at the edge of a flat top
    takes its step on the top and stays up-facing, while a pixel on a wall has a steep step on both sides.
    """
    H, W = image_size
    P = points.reshape(H, W, 3)

    def getStep(axis):
        d = np.diff(P, axis=axis)                                   # steps between neighbours along the axis
        pad = [(0, 0)] * 3
        pad[axis] = (1, 0)
        before = np.pad(d, pad, mode="edge")                        # step from the previous pixel
        pad[axis] = (0, 1)
        after = np.pad(d, pad, mode="edge")                         # step to the next pixel
        return np.where(np.abs(before[..., 2:]) < np.abs(after[..., 2:]), before, after)

    n = np.cross(getStep(1), getStep(0))
    nz = np.abs(n[..., 2]) / (np.linalg.norm(n, axis=-1) + 1e-12)
    return (nz > np.cos(np.radians(prm.SEG_MAX_SLOPE_DEG))).reshape(-1)


def getNeighbourPairs(image_size):
    """
    Returns (a, b): pixel indices of every pair of horizontally or vertically neighbouring pixels in the image.
    """
    H, W = image_size
    idx = np.arange(H * W).reshape(H, W)
    a = np.r_[idx[:, :-1].ravel(), idx[:-1, :].ravel()]          # each pixel and its right / lower neighbour
    b = np.r_[idx[:, 1:].ravel(), idx[1:, :].ravel()]
    return a, b


def getSurfaceLabels(z, keep, image_size):
    """
    Returns one label per pixel (-1 for pixels not kept): connected regions of kept pixels whose neighbours differ in
    height by less than SEG_DEPTH_JUMP (connected components of a graph whose edges are such neighbour pairs).
    """
    a, b = getNeighbourPairs(image_size)
    joined = keep[a] & keep[b] & (np.abs(z[a] - z[b]) < prm.SEG_DEPTH_JUMP)
    n = len(z)
    graph = coo_matrix((np.ones(joined.sum()), (a[joined], b[joined])), shape=(n, n))
    _, labels = connected_components(graph, directed=False)
    return np.where(keep, labels, -1)


def getCoverings(labels, z, image_size):
    """
    Returns {label: set of labels lying on it}: where two regions touch in the image and one is higher by more than
    SEG_DEPTH_JUMP at the border, the higher one lies on the lower one.
    """
    a, b = getNeighbourPairs(image_size)
    la, lb = labels[a], labels[b]
    touch = (la >= 0) & (lb >= 0) & (la != lb)
    a, b, la, lb = a[touch], b[touch], la[touch], lb[touch]
    covers = {}
    for lo, hi, dz in ((la, lb, z[b] - z[a]), (lb, la, z[a] - z[b])):
        on_top = dz > prm.SEG_DEPTH_JUMP
        for l_low, l_high in set(zip(lo[on_top].tolist(), hi[on_top].tolist())):
            covers.setdefault(l_low, set()).add(l_high)
    return covers


def getBorderPixels(image_size):
    """
    Returns a flattened boolean image: True for pixels within BORDER_MARGIN_PX of the image edge.
    """
    H, W = image_size
    m = prm.BORDER_MARGIN_PX
    border = np.ones((H, W), bool)
    border[m:H - m, m:W - m] = False
    return border.reshape(-1)


def getNearHidden(hidden, image_size):
    """
    Returns a flattened boolean image: True for pixels within BORDER_MARGIN_PX of a hidden pixel. A blob there may be
    cut by an ignore box exactly as by the image border (in the task a robot reads pieces next to its own base).
    """
    near = binary_dilation(hidden.reshape(image_size), iterations=prm.BORDER_MARGIN_PX)
    return near.reshape(-1)


def getBlobs(rgb, points, valid, image_size, ignore_boxes, floor_z):
    """
    Returns the list of blobs in one picture (see the top of the file). Regions with fewer than SEG_MIN_POINTS points
    (specks, side walls) or wider than SEG_MAX_EXTENT (not a piece) are dropped.
    """
    keep, hidden = getPieceMask(points, valid, ignore_boxes, floor_z)
    keep &= getUpFacing(points, image_size)
    if not keep.any():
        return []
    labels = getSurfaceLabels(points[:, 2], keep, image_size)
    covers = getCoverings(labels, points[:, 2], image_size)
    border = getBorderPixels(image_size) | getNearHidden(hidden, image_size)

    order = np.argsort(labels, kind="stable")                   # group pixel indices by label
    sorted_labels = labels[order]
    starts = np.flatnonzero(np.r_[True, sorted_labels[1:] != sorted_labels[:-1]])
    blobs, index_of = [], {}
    for s, e in zip(starts, np.r_[starts[1:], len(order)]):
        lab = sorted_labels[s]
        if lab < 0 or e - s < prm.SEG_MIN_POINTS:
            continue
        pix = order[s:e]
        if np.ptp(points[pix, :2], axis=0).max() > prm.SEG_MAX_EXTENT:
            continue
        index_of[lab] = len(blobs)
        blobs.append({"points": points[pix], "rgb": rgb[pix], "pixels": pix, "cut": bool(border[pix].any()),
                      "label": int(lab)})
    for b in blobs:                                             # covering, as indices into the returned list
        on_me = [index_of[l] for l in covers.get(b["label"], ()) if l in index_of]
        b["covered_by"] = on_me
        b["occluded"] = len(on_me) > 0
        del b["label"]
    return blobs


if __name__ == "__main__":
    import robotic as ry #type: ignore
    import matplotlib.pyplot as plt
    from scene_builder import buildScene, placeTestCamera
    from camera import takePicture, getIgnoreBoxes

    C, names, floor_z, _ = buildScene()
    view = ry.CameraView(C)
    placeTestCamera(C, -2.5, 2.5, prm.TEST_CAMERA_HEIGHT, 0., floor_z)
    rgb, points, valid, size = takePicture(view, C, prm.TEST_CAMERA_NAME)
    blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C), floor_z)
    print(f"{len(blobs)} blobs, {sum(b['cut'] for b in blobs)} touching the image border, "
          f"{sum(b['occluded'] for b in blobs)} partly covered by another piece")

    plt.figure(figsize=(8, 6))
    for b in blobs:
        plt.scatter(b["points"][:, 0], b["points"][:, 1], s=0.5, marker="x" if b["cut"] or b["occluded"] else "o")
    plt.gca().set_aspect("equal")
    plt.title("one colour per surface (x = cut by the image border or covered by another piece)")
    plt.show()
