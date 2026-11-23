"""
The 36 letter models, read straight from characters.g (geometry only, no scene and no ground truth).

    loadTemplates()  ->  templates

templates is a dict:
    "symbols"   the 36 symbols in SYMBOLS order
    "points"    per symbol: P x 2 points covering its strokes, in the piece frame, every TEMPLATE_SAMPLE_STEP
    "marks"     per symbol: M x 2 centres of its black glyph-bottom marks, in the piece frame
    "centroid"  per symbol: mean of its stroke points (piece frame); templates are drawn around this point
    "grasp"     per symbol: (grasp point xy, closing angle) of its _grasp marker, in the piece frame
    "sym180"    per symbol: True if it looks the same turned by 180 deg (H, I, N, O, S, X, Z, 0, 2, 5, 8)
    "grids"     {cell size: (stroke grids, mark grids)} each n_symbols x rows x cols, drawn centred on the centroid
"""
import numpy as np
import robotic as ry #type: ignore
import parameters as prm


# ------------------------------------------- 1. RASTERS --------------------------------------------------------------------

def getGridShape(cell, margin_cells=0):
    """
    Returns (rows, cols) of a window of TEMPLATE_HALF_X x TEMPLATE_HALF_Y around a centre, enlarged by margin_cells.
    Rows follow y, columns follow x.
    """
    nx = int(round(2 * prm.TEMPLATE_HALF_X / cell)) + 2 * margin_cells
    ny = int(round(2 * prm.TEMPLATE_HALF_Y / cell)) + 2 * margin_cells
    return ny, nx


def rasterize(xy, cell, margin_cells=0):
    """
    Returns a boolean grid (rows = y, cols = x) of the window around (0, 0): True where at least one point falls.
    """
    ny, nx = getGridShape(cell, margin_cells)
    ix = np.floor((xy[:, 0] + prm.TEMPLATE_HALF_X) / cell).astype(int) + margin_cells
    iy = np.floor((xy[:, 1] + prm.TEMPLATE_HALF_Y) / cell).astype(int) + margin_cells
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    grid = np.zeros((ny, nx), bool)
    grid[iy[ok], ix[ok]] = True
    return grid


def rotatePoints(xy, angle):
    """
    Returns the points expressed in a frame turned by `angle` (i.e. the points rotated by -angle).
    """
    c, s = np.cos(angle), np.sin(angle)
    return np.c_[xy[:, 0] * c + xy[:, 1] * s, -xy[:, 0] * s + xy[:, 1] * c]


def turnPoints(xy, angle):
    """
    Returns the points rotated by +angle (the inverse of rotatePoints).
    """
    return rotatePoints(xy, -angle)


# ------------------------------------------- 2. READING characters.g -------------------------------------------------------

def getStrokePoints(frame):
    """
    Returns points every TEMPLATE_SAMPLE_STEP covering the stroke boxes of one character frame (piece frame).
    Stroke boxes are the children named '<char>_s<k>'; base layers, marks and markers are skipped.
    """
    step = prm.TEMPLATE_SAMPLE_STEP
    pts = []
    for child in frame.getChildren():
        if not child.name[len(frame.name):].startswith("_s") or child.getShapeType() != ry.ST.ssBox:
            continue
        L, W = child.getSize()[:2]
        centre = child.getRelativePosition()[:2]
        q = child.getRelativeQuaternion()                   # rotation about z only
        a = 2 * np.arctan2(q[3], q[0])
        u, v = np.meshgrid(np.arange(-L / 2, L / 2 + 1e-9, step), np.arange(-W / 2, W / 2 + 1e-9, step))
        pts.append(turnPoints(np.c_[u.ravel(), v.ravel()], a) + centre)
    return np.vstack(pts)


def getMarks(frame):
    """
    Returns the centres (piece frame) of the black glyph-bottom marks of one character: children named '<char>_hole<k>'.
    """
    marks = [c.getRelativePosition()[:2] for c in frame.getChildren() if c.name[len(frame.name):].startswith("_hole")]
    return np.array(marks).reshape(-1, 2)


def getGrasp(frame):
    """
    Returns (grasp point xy, closing angle) of the character's '_grasp' marker, in the piece frame.
    """
    g = next(c for c in frame.getChildren() if c.name == frame.name + "_grasp")
    q = g.getRelativeQuaternion()
    return g.getRelativePosition()[:2].copy(), float(2 * np.arctan2(q[3], q[0]))


# ------------------------------------------- 3. LOADING ALL TEMPLATES ------------------------------------------------------

def getMarkGrid(marks, cell, centroid):
    """
    Returns the grid of the black marks of one symbol: each mark drawn as a small cross of DOT_RADIUS.
    """
    r = prm.DOT_RADIUS
    cross = np.array([[0, 0], [r, 0], [-r, 0], [0, r], [0, -r]])
    pts = (marks[:, None, :] + cross[None]).reshape(-1, 2) - centroid
    return rasterize(pts, cell) if len(pts) else np.zeros(getGridShape(cell), bool)


def getSym180(points):
    """
    Returns True if the stroke points look the same after a half turn about their centroid.
    """
    p = points - points.mean(axis=0)
    a, b = rasterize(p, prm.SYM180_GRID_CELL), rasterize(-p, prm.SYM180_GRID_CELL)
    return bool((a & b).sum() / (a | b).sum() > prm.SYM180_THRESHOLD)


def loadTemplates(cells=(prm.COARSE_GRID_CELL, prm.FINE_GRID_CELL)):
    """
    Returns the templates of all 36 symbols (see the top of the file), with grids for each cell size in `cells`.
    """
    M = ry.Config()
    M.addFile(prm.CHARACTERS_FILE)
    t = {"symbols": list(prm.SYMBOLS), "points": [], "marks": [], "centroid": [], "grasp": [], "sym180": []}
    for s in prm.SYMBOLS:
        frame = M.getFrame(prm.CHARACTER_FRAME_PREFIX + s)
        pts = getStrokePoints(frame)
        t["points"].append(pts)
        t["marks"].append(getMarks(frame))
        t["centroid"].append(pts.mean(axis=0))
        t["grasp"].append(getGrasp(frame))
        t["sym180"].append(getSym180(pts))
    t["grids"] = {}
    for cell in cells:
        strokes = np.array([rasterize(p - c, cell) for p, c in zip(t["points"], t["centroid"])], float)
        marks = np.array([getMarkGrid(m, cell, c) for m, c in zip(t["marks"], t["centroid"])], float)
        t["grids"][cell] = (strokes, marks)
    return t


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    t = loadTemplates()
    print("look the same after a half turn:", [s for s, v in zip(t["symbols"], t["sym180"]) if v])
    strokes, marks = t["grids"][prm.FINE_GRID_CELL]
    fig, axes = plt.subplots(4, 9, figsize=(12, 7))
    for k, ax in enumerate(axes.ravel()):
        ax.imshow(strokes[k] + 2 * marks[k], origin="lower", cmap="gray_r")
        ax.set_title(t["symbols"][k])
        ax.axis("off")
    plt.tight_layout()
    plt.show()
