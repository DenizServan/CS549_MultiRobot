"""
The reader: ties the pipeline together, from a camera name to a list of reads.

    readPicture(view, C, camera_name, templates, floor_z, classifier)  ->  list of reads

    camera -> point cloud (camera.py) -> blobs (segmentation.py) -> descriptions (blob.py; black undersides skipped)
           -> symbol + coarse angle (classifier) -> exact pose and fit (refine.py) -> confidence (confidence.py)
    Blobs that one template cannot explain (touching pieces) are split and read again.

Each read is a dict:
    "symbol", "k"   the symbol and its index in SYMBOLS
    "yaw"           angle of the piece frame (radians)
    "xy"            position of the piece origin in the room
    "conf"          confidence (compare with CONF_ACT / CONF_VERIFY / CONF_ACCEPT)
    "alts"          other symbols that scored almost as well
    "precision", "score"   fit checks from refine.py
    "z_top", "tilt", "stacked", "cut", "occluded"   from the blob description
Reads of pieces cut by the image border, covered by another piece or tilted beyond MAX_TILT_DEG get confidence 0:
their outline is incomplete or distorted, so the robot has to look again (or lift the piece on top first).
classifier is classifyTemplate (default) or a cnn.classify_cnn.CnnClassifier; both have the same inputs and outputs.
"""
import numpy as np
import parameters as prm
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs
from blob import describeBlob, subDescription
from classify_template import classifyTemplate
from refine import fineFit, explainedMask
from confidence import coveragePenalty, fitPenalty


def getPointsPerCell(top):
    """
    Returns the average number of outline points per occupied 1 cm cell (far views: few, close-ups: many).
    """
    cells = np.unique(np.floor(top / prm.SEG_GRID_CELL).astype(int), axis=0)
    return len(top) / max(len(cells), 1)


def isUntrusted(desc):
    """
    Returns True if a read of this description must not be trusted: cut by the image border, partly covered by
    another piece, or tilted beyond MAX_TILT_DEG.
    """
    return bool((prm.DISTRUST_CUT and desc["cut"]) or (prm.DISTRUST_OCCLUDED and desc["occluded"])
                or desc["tilt"] > np.radians(prm.MAX_TILT_DEG))


def readDescription(desc, templates, classifier=classifyTemplate, depth=0):
    """
    Returns the list of reads of one blob description: one read, or several if the blob holds touching pieces.
    """
    c = classifier(desc, templates)
    fit = fineFit(desc, templates, c["k"], c["yaw"])
    conf = c["margin"] * coveragePenalty(fit["precision"])
    if c["fit_check"]:                                      # both readers set it (template fit of the answer)
        conf *= fitPenalty(fit["score"], getPointsPerCell(desc["top"]))
    if isUntrusted(desc):
        conf = 0.
    read = {"symbol": templates["symbols"][c["k"]], "k": c["k"], "yaw": fit["yaw"], "xy": fit["xy"], "conf": conf,
            "alts": c["alts"], "precision": fit["precision"], "score": fit["score"], "z_top": desc["z_top"],
            "tilt": desc["tilt"], "stacked": desc["stacked"], "cut": desc["cut"], "occluded": desc["occluded"]}
    if fit["precision"] >= prm.COVERAGE_THRESHOLD or depth >= prm.MAX_SPLIT_DEPTH:
        return [read]

    # touching pieces: read the points this piece explains on their own, and the rest as another blob
    on_top = explainedMask(desc["top"], templates, c["k"], fit["yaw"], fit["xy"])
    on_dark = explainedMask(desc["dark"], templates, c["k"], fit["yaw"], fit["xy"])
    reads = []
    if on_top.sum() >= prm.MIN_SPLIT_POINTS:
        reads += readDescription(subDescription(desc, on_top, on_dark), templates, classifier, prm.MAX_SPLIT_DEPTH)
    if (~on_top).sum() >= prm.MIN_SPLIT_POINTS:
        reads += readDescription(subDescription(desc, ~on_top, ~on_dark), templates, classifier, depth + 1)
    return reads or [read]


def readPicture(view, C, camera_name, templates, floor_z, classifier=classifyTemplate):
    """
    Takes a picture with a camera and returns the reads of every piece in it (see the top of the file).
    """
    rgb, points, valid, size = takePicture(view, C, camera_name)
    reads = []
    blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C, camera_name), floor_z)
    for blob in blobs:
        desc = describeBlob(blob, floor_z, blobs)
        if not desc["underside"]:                           # a black base layer is not a piece top: nothing to read
            reads += readDescription(desc, templates, classifier)
    return reads


if __name__ == "__main__":
    import robotic as ry #type: ignore
    from scene_builder import buildScene, placeTestCamera
    from templates import loadTemplates

    C, names, floor_z, _ = buildScene()
    view = ry.CameraView(C)
    templates = loadTemplates()
    placeTestCamera(C, -2.5, 2.5, prm.TEST_CAMERA_HEIGHT, 0., floor_z)
    for r in readPicture(view, C, prm.TEST_CAMERA_NAME, templates, floor_z):
        print(f"'{r['symbol']}' at ({r['xy'][0]:5.2f}, {r['xy'][1]:5.2f}), yaw {np.degrees(r['yaw']):6.1f} deg, "
              f"conf {r['conf']:.2f}" + (", cut" if r["cut"] else ""))
