"""
CNN reader: the learned replacement for classify_template.py, with the same inputs and outputs.

    classifier = CnnClassifier()
    classifier(description, templates)  ->  {"k", "yaw", "margin", "alts", "fit_check"}

The blob's outline and marks are drawn as a 2 x 64 x 64 image; the network gives probabilities over the 36 symbols and
the 72 angle bins. margin = the smaller of (best minus second symbol probability) and (probability at the best angle
minus at the half-turned angle), mapped onto the template confidence scale by the calibration saved by train.py.
fit_check = True: the reader then also checks the classical template fit of this answer (confidence.fitPenalty),
because the network is over-confident on pieces cut by the image border.
"""
import os
import sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # perception/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                    # perception/cnn/ (model.py)
import parameters as prm
from confidence import calibrate
from model import Net, getInputImage


def getMargins(p_symbol, p_angle, sym180):
    """
    Returns (margin, best angle bin): margin = min(symbol margin, angle margin). The angle margin compares the
    probability around the best bin with the probability around the half-turned bin (0 for symmetric glyphs).
    """
    n, w = prm.CNN_N_ANGLE_BINS, prm.CNN_YAW_NEIGHBOURS
    b = int(np.argmax(p_angle))
    around = lambda c: p_angle[[(c + d) % n for d in range(-w, w + 1)]].sum()
    flipped = 0. if sym180 else around(b + n // 2)
    symbol_margin = p_symbol.max() - np.sort(p_symbol)[-2]
    return float(min(symbol_margin, around(b) - flipped)), b


class CnnClassifier:
    """
    Callable with the signature of classify_template.classifyTemplate.
    """

    def __init__(self, path=prm.CNN_WEIGHTS_FILE):
        saved = torch.load(path, map_location="cpu", weights_only=False)
        self.n_layers = saved["state"]["features.0.0.weight"].shape[1]   # 2: weights trained before the hidden layer
        self.net = Net(n_layers=self.n_layers)
        self.net.load_state_dict(saved["state"])
        self.net.eval()
        self.calibration = saved["calibration"]

    def __call__(self, desc, templates):
        hidden = desc.get("hidden", np.zeros((0, 2)))
        image = getInputImage(desc["top"] - desc["centre"], desc["dark"] - desc["centre"], hidden - desc["centre"])
        with torch.no_grad():
            ls, la = self.net(torch.from_numpy(image[None, :self.n_layers]))
        p_symbol, p_angle = torch.softmax(ls, 1).numpy()[0], torch.softmax(la, 1).numpy()[0]
        k = int(np.argmax(p_symbol))
        margin, b = getMargins(p_symbol, p_angle, templates["sym180"][k])
        # angle: probability-weighted circular mean of the best bin and its neighbours
        n, w = prm.CNN_N_ANGLE_BINS, prm.CNN_YAW_NEIGHBOURS
        bins = [(b + d) % n for d in range(-w, w + 1)]
        a = np.array(bins) * 2 * np.pi / n
        yaw = float(np.arctan2((p_angle[bins] * np.sin(a)).sum(), (p_angle[bins] * np.cos(a)).sum()))
        alts = [templates["symbols"][j] for j in np.argsort(-p_symbol)[:4]
                if j != k and p_symbol[j] > prm.CNN_MIN_RUNNER_UP_PROB]
        return {"k": k, "yaw": yaw, "margin": calibrate(margin, self.calibration), "alts": alts, "fit_check": True}
