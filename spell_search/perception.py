# Classical symbol perception (the baseline the learned classifier will be compared with).
#
#   depth image -> world point cloud -> points standing above the floor, outside tables and robots
#   -> connected components = piece candidates -> top surface + dark bottom marks
#   -> template matching over 36 symbols x 72 rotations x small shifts (templates are built from the
#      stroke boxes in characters.g, so labels are free in simulation)
#   -> fine refinement (1 deg, 5 mm) of the winner -> symbol, yaw, piece origin, confidence
#
# The same reader is used for the coarse read from the mast camera (search) and for the close
# re-read from the wrist camera right before grasping. classify() is the interface a learned classifier
# (CNN / VLM) has to keep; the CNN in cnn.py plugs in through CLASSIFIER (python3 spell_search/run.py --cnn). occupancy() at the end is a cheap depth-only map of the floor for navigation.
import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
from scipy import fft as sfft
import robotic as ry
from config import *
from world import wrap

XR, YR = .10, .155                      # half extent of the template window in the piece frame
SHIFT = 3                               # shifts searched around the centroid alignment (cells)


def raster(xy, res, xr=XR, yr=YR):
    """points (..., 2) in a frame centred on the window -> boolean grid (ny x nx)"""
    nx, ny = int(round(2 * xr / res)), int(round(2 * yr / res))
    ix = np.floor((xy[:, 0] + xr) / res).astype(int)
    iy = np.floor((xy[:, 1] + yr) / res).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    g = np.zeros((ny, nx), bool)
    g[iy[ok], ix[ok]] = True
    return g


def rot(xy, a):
    """express points in a frame turned by a (i.e. rotate them by -a)"""
    c, s = np.cos(a), np.sin(a)
    return np.c_[xy[:, 0] * c + xy[:, 1] * s, -xy[:, 0] * s + xy[:, 1] * c]


class Templates:
    """Templates of all symbols, made from the stroke boxes and bottom marks in the scene."""

    def __init__(self, C, pieces, symbol):
        self.symbols, self.pts, self.holes, self.grasp = [], [], [], {}
        seen = set()
        for n in pieces:
            s = symbol[n]
            if s in seen:
                continue
            seen.add(s)
            strokes, holes = [], []
            for ch in C.getFrame(n).getChildren():
                name = ch.name[len(n):]
                rel = ch.getRelativePosition()
                if name.startswith("_s") and ch.getShapeType() == ry.ST.ssBox:
                    L, Wd = ch.getSize()[:2]
                    q = ch.getRelativeQuaternion()
                    a = 2 * np.arctan2(q[3], q[0])
                    u, v = np.meshgrid(np.arange(-L / 2, L / 2 + 1e-9, .002), np.arange(-Wd / 2, Wd / 2 + 1e-9, .002))
                    u, v = u.ravel(), v.ravel()
                    strokes.append(np.c_[rel[0] + u * np.cos(a) - v * np.sin(a), rel[1] + u * np.sin(a) + v * np.cos(a)])
                elif name.startswith("_hole"):
                    holes.append(rel[:2].copy())
                elif name == "_grasp":
                    q = ch.getRelativeQuaternion()
                    self.grasp[s] = (rel[:2].copy(), 2 * np.arctan2(q[3], q[0]))
            self.symbols.append(s)
            self.pts.append(np.vstack(strokes))
            self.holes.append(np.array(holes).reshape(-1, 2))
        self.centres = np.array([p.mean(0) for p in self.pts])
        self.T = [self.stroke_grid(k, GRID) for k in range(len(self.symbols))]
        self.H = [self.hole_grid(k, GRID) for k in range(len(self.symbols))]
        self.Tflip = np.array(self.T)[:, ::-1, ::-1].copy()       # correlation = convolution with the flipped template
        self.Hflip = np.array(self.H)[:, ::-1, ::-1].copy()
        self.Tsum = np.array([t.sum() for t in self.T])
        self._spec = {}

        # glyphs that look the same after a half turn (S, N, Z, H, O, X, I, 0, 8 ...)
        self.sym180 = {}
        for k, s in enumerate(self.symbols):
            a = raster(self.pts[k] - self.centres[k], .005)
            b = raster(-(self.pts[k] - self.centres[k]), .005)
            self.sym180[s] = (a & b).sum() / (a | b).sum() > .85

    def correlate(self, O, which):
        """valid correlation of grid O with all templates (strokes 'T' or marks 'H'): (n_symbols, rows, cols)"""
        F = self.Tflip if which == "T" else self.Hflip
        shape = tuple(sfft.next_fast_len(n, True) for n in (O.shape[0] + F.shape[1] - 1, O.shape[1] + F.shape[2] - 1))
        key = (which, shape)
        if key not in self._spec:
            self._spec[key] = sfft.rfft2(F, s=shape, axes=(1, 2))
        full = sfft.irfft2(sfft.rfft2(O, s=shape)[None] * self._spec[key], s=shape, axes=(1, 2), workers=-1)
        return np.rint(full[:, F.shape[1] - 1:O.shape[0], F.shape[2] - 1:O.shape[1]])

    def stroke_grid(self, k, res):
        return raster(self.pts[k], res).astype(float)

    def hole_grid(self, k, res):
        g = np.zeros_like(self.stroke_grid(k, res), dtype=bool)
        for h in self.holes[k]:
            g |= raster(h[None] + .0067 * np.array([[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]]), res)
        return g.astype(float)


def segment(P, rgb, valid, floor_top, exclude):
    """piece candidates in a point cloud. exclude: list of (centre xy, half extents xy) boxes to ignore"""
    z = P[:, 2]
    m = valid & (z > floor_top + .012) & (z < floor_top + .25)
    for c, e in exclude:
        m &= ~np.all(np.abs(P[:, :2] - c) < e, axis=1)
    pts, col = P[m], rgb.reshape(-1, 3)[m].astype(int)
    if len(pts) == 0:
        return []
    lo = pts[:, :2].min(0)
    ij = np.floor((pts[:, :2] - lo) / .01).astype(int)
    occ = np.zeros(ij.max(0) + 1, bool)
    occ[ij[:, 0], ij[:, 1]] = True
    lab, n = ndimage.label(ndimage.binary_dilation(occ, iterations=2))
    pl = lab[ij[:, 0], ij[:, 1]]
    out = []
    for k in range(1, n + 1):
        sel = pl == k
        if sel.sum() < 25:
            continue
        p, c = pts[sel], col[sel]
        top = p[:, 2].max()
        upper = p[:, 2] > top - .014                 # top surface of the uppermost piece
        dark = upper & (c.max(1) < 25)                # the bottom marks are black; stroke edges blend with the floor and stay above this
        ext = np.ptp(p[upper, :2], axis=0)
        out.append({"xy": p[upper, :2].mean(0), "top": p[upper, :2], "dark": p[dark, :2],
                    "z_top": top, "stacked": bool(top > floor_top + .065), "extent": ext, "n": int(sel.sum())})
    return out


def _match(tpl, k, O, D, res, shift):
    """best (score, shift, precision) of template k against observed grids O (strokes) and D (dark marks),
    both rasterised relative to the observed centroid in a window enlarged by M cells per side"""
    T, H = (tpl.T[k], tpl.H[k]) if res == GRID else (tpl.stroke_grid(k, res), tpl.hole_grid(k, res))
    inter = np.rint(fftconvolve(O, T[::-1, ::-1], mode="valid"))   # all offsets of the template inside the window
    M = (O.shape[1] - T.shape[1]) // 2
    o0 = M - np.round(tpl.centres[k][::-1] / res).astype(int)     # (row, col) offset of centroid alignment
    r0, r1 = max(o0[0] - shift, 0), min(o0[0] + shift + 1, inter.shape[0])
    c0, c1 = max(o0[1] - shift, 0), min(o0[1] + shift + 1, inter.shape[1])
    win = inter[r0:r1, c0:c1]
    iou = win / (O.sum() + T.sum() - win + 1e-9)
    if D.sum() > 0:
        hit = np.rint(fftconvolve(D, H[::-1, ::-1], mode="valid"))[r0:r1, c0:c1] / D.sum()
        iou = iou + HOLE_W * (2 * hit - 1)           # +HOLE_W if all dark points sit on the marks, -HOLE_W if none
    i, j = np.unravel_index(np.argmax(iou), iou.shape)
    off = np.array([r0 + i, c0 + j])
    return iou[i, j], off - M, win[i, j] / max(O.sum(), 1.)


def _grids(top, dark, c0, a, res, M):
    xr, yr = XR + M * res, YR + M * res
    return raster(rot(top - c0, a), res, xr, yr).astype(float), raster(rot(dark - c0, a), res, xr, yr).astype(float)


# The reader used for every blob: None = the classical template search below; run.py --cnn sets it to
# cnn.Classifier() (same signature, same result dict).
CLASSIFIER = None


def classify(tpl, cand):
    return (CLASSIFIER or classify_template)(tpl, cand)


def classify_template(tpl, cand):
    """symbol, yaw (of the piece frame), piece origin xy and confidence of one candidate"""
    top, dark = cand["top"], cand["dark"]
    c0 = top.mean(0)
    M = SHIFT + int(np.ceil(np.abs(tpl.centres).max() / GRID)) + 1
    S = np.full((len(ANGLES), len(tpl.symbols)), -1.)
    o0 = M - np.round(tpl.centres[:, ::-1] / GRID).astype(int)     # per symbol (row, col) of centroid alignment
    for ai, a in enumerate(ANGLES):
        O, D = _grids(top, dark, c0, a, GRID, M)
        # all 36 templates at all offsets at once (FFT, template spectra cached); keep shifts near the alignment
        inter = tpl.correlate(O, "T")
        hits = tpl.correlate(D, "H") if D.sum() > 0 else None
        for k in range(len(tpl.symbols)):
            r0, c0_ = o0[k] - SHIFT
            w = inter[k, r0:r0 + 2 * SHIFT + 1, c0_:c0_ + 2 * SHIFT + 1]
            sc = w / (O.sum() + tpl.Tsum[k] - w + 1e-9)
            if hits is not None:
                sc = sc + HOLE_W * (2 * hits[k, r0:r0 + 2 * SHIFT + 1, c0_:c0_ + 2 * SHIFT + 1] / D.sum() - 1)
            S[ai, k] = sc.max()
    ai, k = np.unravel_index(np.argmax(S), S.shape)
    s, yaw = tpl.symbols[k], ANGLES[ai]
    comp = -1.                                         # best hypothesis that would put a different glyph image on the table
    for a2 in range(len(ANGLES)):
        dyaw = abs(wrap(ANGLES[a2] - yaw))
        for k2, s2 in enumerate(tpl.symbols):
            same = s2 == s and (dyaw < np.radians(25) or (tpl.sym180[s] and abs(dyaw - np.pi) < np.radians(25)))
            if not same:
                comp = max(comp, S[a2, k2])
    best = S[ai, k]
    # fine refinement of the winner: 1 deg, 5 mm
    res = GRID / 2
    Mf = 2 * M
    fine = []
    for da in np.radians(np.arange(-4, 5, 1.)):
        O, D = _grids(top, dark, c0, yaw + da, res, Mf)
        sc, off, prec = _match(tpl, k, O, D, res, 2 * SHIFT + 2)
        fine.append((sc, yaw + da, off, prec))
    sc, yaw, off, prec = max(fine, key=lambda x: x[0])
    conf = float((best - comp) / max(best, 1e-6))
    if prec < .85:                                     # the blob holds more than one piece (touching / overlapping)
        conf *= max(0., (prec - .6) / .25)
    # piece origin: the template window's centre, moved by the offset, turned back by yaw
    d = off[::-1] * res                                # (x, y) in the turned frame
    c, si = np.cos(yaw), np.sin(yaw)
    origin = c0 + np.array([c * d[0] - si * d[1], si * d[0] + c * d[1]])
    # other symbols that fit almost as well (kept on the map: a needed one may be verified later)
    per_symbol = S.max(0)
    alts = [tpl.symbols[j] for j in np.argsort(-per_symbol)[:4] if tpl.symbols[j] != s and per_symbol[j] > .85 * best]
    return {"symbol": s, "yaw": float(wrap(yaw)), "xy": origin, "conf": conf, "score": float(best),
            "stacked": cand["stacked"], "z_top": float(cand["z_top"]), "alts": alts, "prec": float(prec)}


def explained(tpl, x, pts, tol=.012):
    """mask of the points that lie on the strokes of the template placed at x (symbol, xy, yaw)"""
    if len(pts) == 0:
        return np.zeros(0, bool)
    k = tpl.symbols.index(x["symbol"])
    loc = rot(pts - x["xy"], x["yaw"])                      # points in the frame of the fitted piece
    occ = raster(tpl.pts[k], .004)
    occ = ndimage.binary_dilation(occ, iterations=int(np.ceil(tol / .004)))
    nx, ny = occ.shape[1], occ.shape[0]
    ix = np.floor((loc[:, 0] + XR) / .004).astype(int)
    iy = np.floor((loc[:, 1] + YR) / .004).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    m = np.zeros(len(pts), bool)
    m[ok] = occ[iy[ok], ix[ok]]
    return m


def read_candidate(tpl, cand, depth=0):
    """classify a blob; if it holds touching pieces, explain the best one and read the rest again"""
    x = classify(tpl, cand)
    if x["prec"] >= .85 or depth >= 2:
        return [x]
    m, md = explained(tpl, x, cand["top"]), explained(tpl, x, cand["dark"])
    out = []
    if m.sum() > 40:
        x = classify(tpl, {**cand, "top": cand["top"][m], "dark": cand["dark"][md]})
        out.append(x)
    rest = {**cand, "top": cand["top"][~m], "dark": cand["dark"][~md]}
    if (~m).sum() > 60 and np.ptp(rest["top"], axis=0).max() > .08:
        out += read_candidate(tpl, rest, depth + 1)
    return out


def read(world, tpl, cam, exclude):
    rgb, P, valid = world.render(cam)
    out = []
    for c in segment(P, rgb, valid, world.floor_top, exclude):
        if c["extent"].max() < .60:
            out += [x | {"blob_xy": c["xy"]} for x in read_candidate(tpl, c)]
    return out


# depth-only occupancy for navigation (no classification, so it is cheap enough to run while driving)
def occupancy(world, cam, planner, exclude, skip=()):
    """cells of the planner grid seen by the camera, and those holding a piece (points 1.2-25 cm above the floor).
    exclude: (centre, half extents) boxes to ignore (robots, tables); skip: (xy, radius) discs not to update
    (the other robot's arm may be down there)"""
    rgb, P, valid = world.render(cam)
    m = valid & (P[:, 2] < world.floor_top + .25)
    for c, e in exclude:
        m &= ~np.all(np.abs(P[:, :2] - c) < e, axis=1)
    for c, rad in skip:
        m &= np.sum((P[:, :2] - c) ** 2, axis=1) > rad ** 2
    pts = P[m]
    ij = np.round((pts[:, :2] - planner.room[[0, 2]]) / planner.res).astype(int)
    ok = (ij[:, 0] >= 0) & (ij[:, 0] < planner.nx) & (ij[:, 1] >= 0) & (ij[:, 1] < planner.ny)
    ij, pts = ij[ok], pts[ok]
    seen = np.zeros((planner.nx, planner.ny), int)
    np.add.at(seen, (ij[:, 0], ij[:, 1]), 1)
    high = pts[:, 2] > world.floor_top + .012
    occ = np.zeros_like(seen)
    np.add.at(occ, (ij[high, 0], ij[high, 1]), 1)
    return seen >= 3, occ >= 3                    # a few points per cell: no single noisy pixel decides
