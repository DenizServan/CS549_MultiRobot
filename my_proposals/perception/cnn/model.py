"""
The CNN symbol reader's network and its input image.

    getInputImage(top, dark, hidden) -> 3 x 64 x 64 image of a blob (layers: outline points, black marks, hidden
                                        region = where a piece lying on it covers it)
    Net                       ->  image -> (36 symbol scores, 72 angle scores)
    getAngleTarget(yaw, sym180) -> soft target over the 72 angle bins used in training
"""
import os
import sys
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # perception/ (parameters.py)
import parameters as prm
from confidence import wrapAngle


def getInputImage(top, dark, hidden=None):
    """
    Returns the CNN_INPUT_LAYERS x S x S image (S = CNN_IMAGE_SIZE_PX, CNN_RESOLUTION per pixel) of points given
    relative to the blob centre: outline, black marks, hidden region (empty if none). Rows follow y and columns follow
    x (room axes), so turning the points turns the image. The hidden layer tells the network where missing strokes
    may simply be covered.
    """
    size, res = prm.CNN_IMAGE_SIZE_PX, prm.CNN_RESOLUTION
    img = np.zeros((prm.CNN_INPUT_LAYERS, size, size), np.float32)
    hidden = np.zeros((0, 2)) if hidden is None else hidden
    for layer, pts in enumerate((top, dark, hidden)):
        if len(pts) == 0:
            continue
        ij = np.floor(pts / res + size / 2).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 0] < size) & (ij[:, 1] >= 0) & (ij[:, 1] < size)
        img[layer, ij[ok, 1], ij[ok, 0]] = 1.
    return img


class Net(nn.Module):
    """
    Four blocks of (3x3 conv, batch norm, ReLU) x 2 + 2x2 max-pool: 64 -> 32 -> 16 -> 8 -> 4 pixels,
    then a 256-unit dense layer and two heads: symbol (36 scores) and angle (72 bins of 5 deg).
    """

    def __init__(self, n_symbols=prm.N_SYMBOLS, n_angles=prm.CNN_N_ANGLE_BINS, n_layers=prm.CNN_INPUT_LAYERS):
        super().__init__()

        def block(c_in, c_out):
            return nn.Sequential(nn.Conv2d(c_in, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
                                 nn.Conv2d(c_out, c_out, 3, padding=1), nn.BatchNorm2d(c_out), nn.ReLU(),
                                 nn.MaxPool2d(2))
        self.features = nn.Sequential(block(n_layers, 32), block(32, 64), block(64, 128), block(128, 128))
        side = prm.CNN_IMAGE_SIZE_PX // 16
        self.trunk = nn.Sequential(nn.Flatten(), nn.Linear(128 * side * side, 256), nn.ReLU(), nn.Dropout(0.3))
        self.symbol_head = nn.Linear(256, n_symbols)
        self.angle_head = nn.Linear(256, n_angles)

    def forward(self, x):
        h = self.trunk(self.features(x))
        return self.symbol_head(h), self.angle_head(h)


def getAngleTarget(yaw, sym180):
    """
    Returns the soft training target over the angle bins: a Gaussian CNN_YAW_SIGMA_BINS wide around the true angle;
    for glyphs that look the same after a half turn, half of the mass sits at yaw + 180 deg.
    """
    n = prm.CNN_N_ANGLE_BINS
    centres = np.arange(n) * 2 * np.pi / n

    def bump(a):
        d = np.abs(wrapAngle(centres - a)) / (2 * np.pi / n)
        w = np.exp(-0.5 * (d / prm.CNN_YAW_SIGMA_BINS) ** 2)
        return w / w.sum()
    return 0.5 * (bump(yaw) + bump(yaw + np.pi)) if sym180 else bump(yaw)
