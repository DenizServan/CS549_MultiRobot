# Learned symbol perception: a small CNN that replaces the template search over 36 symbols x 72 rotations.
#
#   blob (top-surface points + dark bottom marks, from perception.segment) -> 2-channel top view image
#   (64 x 64, 5 mm per pixel, centred on the blob) -> CNN -> p(symbol) (36) and p(yaw) (72 bins of 5 deg)
#   -> pose of the winner refined like the classical reader (1 deg, 5 mm; perception._match), which also gives
#      the precision used to detect touching pieces
#
# What it replaces: the exhaustive template correlation that decides symbol and coarse yaw.
# What it keeps: segmentation, the fine pose fit and the touching-piece test of the classical reader, and the
#   fit score of that pose fit as a check on the CNN's confidence (without it, the CNN trusted wrong reads of
#   pieces cut by the image border).
# What it assumes: pieces look like the simulated ones (it is trained on rendered views only).
#
# classify_cnn() returns the same dict as perception.classify(), so the rest of the system does not change.
# Its confidence is mapped onto the scale of the template reader (calibrated in cnn_train.py), so the
# thresholds CONF_ACT / CONF_VERIFY / CONF_ACCEPT in config.py keep their meaning.
import os
import time
import numpy as np
import torch
import torch.nn as nn

from config import *
from world import wrap

HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS = os.path.join(HERE, "cnn_weights.pt")
RES, SIZE = .005, 64                     # 5 mm per pixel, 32 x 32 cm window (a piece is 12 x 24 cm)
N_YAW = 72                               # yaw bins of 5 deg
# Fit check (the CNN is over-confident on pieces cut by the image border): the score of the fine template fit of
# the CNN's answer must be high, or the confidence is scaled down (linear ramp from lo to hi). The score scale
# depends on the point density (mast: ~2 points per cm^2, wrist: ~20), so two ramps, measured on cnn_train.npz:
# mast reads with score >= .40 are wrong 0.8 % of the time, wrist reads with score >= .70 1.1 % of the time.
FIT_SPARSE, FIT_DENSE, DENSE = (.30, .40), (.55, .70), 4.   # (lo, hi) ramps; DENSE: points per cm^2 for the
                                                           # dense ramp
torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))


def raster(top, dark, res=RES, size=SIZE):
    """points relative to the blob centre (N x 2) -> 2 x size x size float image (strokes, dark marks).
    Row index grows with y, column with x (world axes), so turning the points turns the image."""
    img = np.zeros((2, size, size), np.float32)
    for ch, pts in enumerate((top, dark)):
        if len(pts) == 0:
            continue
        ij = np.floor(pts / res + size / 2).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 0] < size) & (ij[:, 1] >= 0) & (ij[:, 1] < size)
        img[ch, ij[ok, 1], ij[ok, 0]] = 1.
    return img


class Net(nn.Module):
    def __init__(self, n_sym=36, n_yaw=N_YAW):
        super().__init__()
        def block(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                                 nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
        self.features = nn.Sequential(block(2, 32), block(32, 64), block(64, 128), block(128, 128))   # 64 -> 4
        self.trunk = nn.Sequential(nn.Flatten(), nn.Linear(128 * 4 * 4, 256), nn.ReLU(), nn.Dropout(.3))
        self.sym = nn.Linear(256, n_sym)
        self.yaw = nn.Linear(256, n_yaw)

    def forward(self, x):
        h = self.trunk(self.features(x))
        return self.sym(h), self.yaw(h)


def yaw_target(yaw, sym180, sigma=1.):
    """soft target over the yaw bins: a Gaussian around the true yaw; for a glyph that looks the same after a
    half turn, half of the mass also around yaw + 180 deg"""
    centres = np.arange(N_YAW) * 2 * np.pi / N_YAW
    def g(a):
        d = np.abs(wrap(centres - a)) / (2 * np.pi / N_YAW)
        w = np.exp(-.5 * (d / sigma) ** 2)
        return w / w.sum()
    t = g(yaw)
    return .5 * (t + g(yaw + np.pi)) if sym180 else t


def calibrate(margin, cal):
    """CNN margin -> template confidence scale: piecewise linear through the calibration points"""
    return float(np.interp(margin, cal["margin"], cal["conf"]))


class Classifier:
    """callable with the signature of perception.classify(tpl, cand)"""

    def __init__(self, path=WEIGHTS):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        self.symbols = list(ck["symbols"])
        self.net = Net(len(self.symbols))
        self.net.load_state_dict(ck["state"])
        self.net.eval()
        self.cal = ck["calibration"]
        self.sym180 = ck["sym180"]
        self.calls, self.seconds = 0, 0.

    def predict(self, imgs):
        with torch.no_grad():
            ls, ly = self.net(torch.from_numpy(np.asarray(imgs)))
        return torch.softmax(ls, 1).numpy(), torch.softmax(ly, 1).numpy()

    def margins(self, ps, py, k):
        """symbol margin (best - second symbol) and yaw margin (mass at the best yaw - mass of the
        half-turned yaw that would put the glyph upside down; 0 for glyphs that look the same that way)"""
        p2 = np.sort(ps)[-2]
        b = int(np.argmax(py))
        near = lambda c: py[[(c + d) % N_YAW for d in range(-2, 3)]].sum()
        flip = 0. if self.sym180[self.symbols[k]] else near(b + N_YAW // 2)
        return ps[k] - p2, near(b) - flip, b

    def __call__(self, tpl, cand):
        from perception import _grids, _match, SHIFT        # the classical fine pose fit
        t0 = time.time()
        top, dark = cand["top"], cand["dark"]
        c0 = top.mean(0)
        ps, py = self.predict(raster(top - c0, dark - c0)[None])
        ps, py = ps[0], py[0]
        k = int(np.argmax(ps))
        s = self.symbols[k]
        m_sym, m_yaw, b = self.margins(ps, py, k)
        # yaw: circular mean over the best bin and its neighbours
        idx = [(b + d) % N_YAW for d in range(-2, 3)]
        a = np.array(idx) * 2 * np.pi / N_YAW
        yaw = float(np.arctan2((py[idx] * np.sin(a)).sum(), (py[idx] * np.cos(a)).sum()))
        # fine pose fit of the winner (as in perception.classify): 1 deg, 5 mm
        kt = tpl.symbols.index(s)
        res = GRID / 2
        M = SHIFT + int(np.ceil(np.abs(tpl.centres).max() / GRID)) + 1
        fine = []
        for da in np.radians(np.arange(-6, 7, 1.)):
            O, D = _grids(top, dark, c0, yaw + da, res, 2 * M)
            sc, off, prec = _match(tpl, kt, O, D, res, 2 * SHIFT + 2)
            fine.append((sc, yaw + da, off, prec))
        sc, yaw, off, prec = max(fine, key=lambda x: x[0])
        conf = calibrate(min(m_sym, m_yaw), self.cal)
        dens = len(top) / max(len(set(map(tuple, np.floor(top / .01).astype(int)))), 1)
        lo, hi = FIT_DENSE if dens >= DENSE else FIT_SPARSE
        conf *= float(np.clip((sc - lo) / (hi - lo), 0., 1.))   # fit check: a cut / misread piece fits badly
        if prec < .85:                                     # touching / overlapping pieces, as in the classical reader
            conf *= max(0., (prec - .6) / .25)
        d = off[::-1] * res
        c, si = np.cos(yaw), np.sin(yaw)
        origin = c0 + np.array([c * d[0] - si * d[1], si * d[0] + c * d[1]])
        alts = [self.symbols[j] for j in np.argsort(-ps)[:4] if j != k and ps[j] > .1]
        self.calls += 1
        self.seconds += time.time() - t0
        return {"symbol": s, "yaw": float(wrap(yaw)), "xy": origin, "conf": conf, "score": float(sc),
                "stacked": cand["stacked"], "z_top": float(cand["z_top"]), "alts": alts, "prec": float(prec),
                "p_symbol": float(ps[k])}
