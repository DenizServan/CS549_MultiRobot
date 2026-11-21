# Train the CNN symbol classifier (cnn.py) on blobs from cnn_data.py, calibrate its confidence and save
# spell_search/cnn_weights.pt.
#
#   python3 spell_search/cnn_train.py --data data/cnn_train.npz [--epochs 25]
#
# Augmentation (free, because the input is a point set): any rotation about the vertical (the yaw label turns
# with it), dropped points (the mast camera sees a piece with far fewer points than the wrist camera),
# 2 mm jitter and a small shift of the centre.
# The last scenes of the training data are held out (validation): they pick the best epoch and calibrate the
# confidence so that the thresholds in config.py keep their meaning (see calibration()).
import os
import sys
import time
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from world import wrap
from cnn import Net, raster, yaw_target, N_YAW, WEIGHTS

SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def sym180_table():
    """glyphs that look the same after a half turn, from the templates (as the classical reader decides it)"""
    from world import World
    from perception import Templates
    W = World(seed=0)
    tpl = Templates(W.C, W.pieces, W.symbol)
    return {s: bool(v) for s, v in tpl.sym180.items()}


def load(path):
    d = np.load(path, allow_pickle=True)
    assert list(d["symbols"]) == SYMBOLS, "symbol order differs from cnn_data.py"
    return [s for s in d["samples"] if s["label"] >= 0 and not s["partial"]]


def augment(s, rng):
    th = rng.uniform(-np.pi, np.pi)
    R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])      # row vectors: p @ R = rotated p
    keep = rng.uniform(.35, 1.)
    shift = rng.normal(0, .008, 2)
    out = []
    for pts in (s["top"], s["dark"]):
        pts = pts[rng.random(len(pts)) < keep] if len(pts) else pts
        out.append(pts @ R + rng.normal(0, .002, pts.shape) + shift)
    return out[0], out[1], s["yaw"] + th


def batch(samples, sym180, rng=None):
    X, ys, yy = [], [], []
    for s in samples:
        top, dark, yaw = augment(s, rng) if rng is not None else (s["top"], s["dark"], s["yaw"])
        X.append(raster(top, dark))
        ys.append(s["label"])
        yy.append(yaw_target(yaw, sym180[SYMBOLS[s["label"]]]))
    return torch.from_numpy(np.stack(X)), torch.tensor(ys), torch.from_numpy(np.stack(yy).astype(np.float32))


def evaluate(net, samples, sym180):
    """symbol accuracy, symbol + yaw accuracy (within 10 deg, or 180 deg off for half-turn glyphs), margins"""
    net.eval()
    from cnn import Classifier
    clf = Classifier.__new__(Classifier)
    clf.symbols, clf.sym180 = SYMBOLS, sym180
    rows = []
    with torch.no_grad():
        for i in range(0, len(samples), 256):
            X, ys, _ = batch(samples[i:i + 256], sym180)
            ls, ly = net(X)
            ps, py = torch.softmax(ls, 1).numpy(), torch.softmax(ly, 1).numpy()
            for j, s in enumerate(samples[i:i + 256]):
                k = int(np.argmax(ps[j]))
                ms, my, b = clf.margins(ps[j], py[j], k)
                dy = abs(wrap(b * 2 * np.pi / N_YAW - s["yaw"]))
                yaw_ok = dy < np.radians(10) or (sym180[SYMBOLS[k]] and abs(dy - np.pi) < np.radians(10))
                rows.append((k == s["label"], k == s["label"] and yaw_ok, min(ms, my), s["kind"]))
    net.train()
    return rows


def threshold(rows, kind, max_err):
    """smallest margin above which the reads of this camera are wrong at most max_err of the time"""
    r = sorted([x for x in rows if x[3] == kind], key=lambda x: -x[2])
    best, wrong = 1., 0
    for i, (_, ok, m, _) in enumerate(r):
        wrong += not ok
        if wrong / (i + 1) <= max_err:
            best = m
    return best


def calibration(rows):
    """map the CNN margin onto the template confidence scale used by config.py:
    CONF_ACCEPT (a wrist read is trusted) <- margin where wrist reads are wrong <= 1 % of the time
    CONF_ACT    (a mast read is worth driving to) <- margin where mast reads are wrong <= 3 % of the time
    CONF_VERIFY (worth a closer look) <- half of the accept margin"""
    m_acc = threshold(rows, "wrist", .01)
    m_act = max(threshold(rows, "mast", .03), m_acc + .01)
    m_ver = .5 * m_acc
    pts = sorted({0.: 0., m_ver: CONF_VERIFY, m_acc: CONF_ACCEPT, m_act: CONF_ACT, 1.: 1.}.items())
    m, c = zip(*pts)
    return {"margin": np.array(m), "conf": np.array(c)}


def main():
    data = arg("--data", "data/cnn_train.npz")
    epochs = int(arg("--epochs", 25))
    bs = 64
    rng = np.random.default_rng(0)
    torch.manual_seed(0)
    sym180 = sym180_table()
    S = load(data)
    seeds = sorted({s["seed"] for s in S})
    val_seeds = set(seeds[-max(1, len(seeds) // 5):])
    train = [s for s in S if s["seed"] not in val_seeds]
    val = [s for s in S if s["seed"] in val_seeds]
    print(f"{len(train)} training blobs ({len(seeds) - len(val_seeds)} scenes), {len(val)} validation blobs "
          f"(scenes {sorted(val_seeds)})")
    net = Net(len(SYMBOLS))
    opt = torch.optim.AdamW(net.parameters(), 2e-3, weight_decay=1e-4)
    steps = epochs * (len(train) // bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-3, total_steps=steps)
    best = (-1, None)
    t0 = time.time()
    for ep in range(epochs):
        order = rng.permutation(len(train))
        loss_sum = 0.
        for i in range(len(train) // bs):
            X, ys, yy = batch([train[j] for j in order[i * bs:(i + 1) * bs]], sym180, rng)
            ls, ly = net(X)
            loss = F.cross_entropy(ls, ys) + F.cross_entropy(ly, yy)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            loss_sum += loss.item()
        rows = evaluate(net, val, sym180)
        acc = np.mean([r[0] for r in rows])
        acc_yaw = np.mean([r[1] for r in rows])
        print(f"epoch {ep + 1:2d}: loss {loss_sum / (len(train) // bs):.3f}, validation symbol {100 * acc:.1f} %, "
              f"symbol + yaw {100 * acc_yaw:.1f} % ({time.time() - t0:.0f} s)", flush=True)
        if acc_yaw > best[0]:
            best = (acc_yaw, {k: v.clone() for k, v in net.state_dict().items()})
    net.load_state_dict(best[1])
    rows = evaluate(net, val, sym180)
    cal = calibration(rows)
    print("calibration (margin -> confidence):", ", ".join(f"{m:.3f}->{c:.2f}" for m, c in zip(cal["margin"], cal["conf"])))
    torch.save({"state": net.state_dict(), "symbols": SYMBOLS, "sym180": sym180, "calibration": cal,
                "val_symbol_yaw_acc": best[0], "train_data": os.path.basename(data)}, WEIGHTS)
    print(f"saved {WEIGHTS} (validation symbol + yaw {100 * best[0]:.1f} %)")


if __name__ == "__main__":
    main()
