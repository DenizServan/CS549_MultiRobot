"""
Trains the CNN reader on the blobs from dataset.py, calibrates its confidence and saves cnn/cnn_weights.pt.

    python3 perception/cnn/train.py                      uses cnn/data/train_a.npz and train_b.npz (task scenes)
    python3 perception/cnn/train.py --data train_a train_b --epochs 25

Only whole, labelled pieces are used. The last CNN_VALIDATION_SHARE of the scenes of every file are held out: they
choose the best epoch and calibrate the confidence (on the CONF_* scale of parameters.py). The thresholds the robots
use are measured afterwards on other scenes (evaluate.py --seeds 80-89 -> READER_THRESHOLDS). Augmentation (free, the input is a point set): random rotation (the angle label
turns with it), dropped points (far views see far fewer points than close-ups), jitter and a small centre shift.
"""
import os
import sys
import argparse
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # perception/
import parameters as prm
from confidence import wrapAngle
from templates import loadTemplates
from model import Net, getInputImage, getAngleTarget
from classify_cnn import getMargins


# ------------------------------------------- 1. DATA ---------------------------------------------------------------------

def loadSamples(name):
    """
    Returns the whole, labelled samples of cnn/data/<name>.npz.
    """
    data = np.load(os.path.join(prm.CNN_DATA_DIR, name + ".npz"), allow_pickle=True)["samples"]
    for s in data:
        s.setdefault("hidden", np.zeros((0, 2), np.float32))           # data made before the hidden layer existed
    return [s for s in data if s["label"] >= 0 and not s["cut"]]


def addFakeCover(top, dark, hidden, rng):
    """
    Returns (top, dark, hidden) with a fake covering piece: a disc (radius in CNN_OCCLUDE_RADIUS) at a random outline
    point; the points under it are removed and the disc becomes hidden. Unchanged if it would hide over half the
    outline. Teaches the network to read pieces with covered parts from the room data too.
    """
    if len(top) < 10:
        return top, dark, hidden
    c = top[rng.integers(len(top))]
    r = rng.uniform(*prm.CNN_OCCLUDE_RADIUS)
    if (np.linalg.norm(top - c, axis=1) < r).mean() > 0.5:
        return top, dark, hidden
    g = np.arange(-r, r + 1e-9, prm.CNN_RESOLUTION)
    disc = np.array([(x, y) for x in g for y in g if x * x + y * y <= r * r]) + c
    return (top[np.linalg.norm(top - c, axis=1) >= r], dark[np.linalg.norm(dark - c, axis=1) >= r] if len(dark) else dark,
            np.vstack([hidden, disc]).astype(np.float32))


def augment(sample, rng):
    """
    Returns (outline, marks, hidden, yaw) of a randomly turned, thinned, jittered and shifted copy of a sample, with a
    fake covering piece for a share CNN_OCCLUDE_SHARE of the samples.
    """
    th = rng.uniform(-np.pi, np.pi)
    R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])      # points as rows: p @ R turns p by +th
    keep = rng.uniform(*prm.CNN_KEEP_RANGE)
    shift = rng.normal(0., prm.CNN_SHIFT, 2)
    top, dark, hidden = sample["top"], sample["dark"], sample["hidden"]
    if rng.random() < prm.CNN_OCCLUDE_SHARE:
        top, dark, hidden = addFakeCover(top, dark, hidden, rng)
    out = []
    for pts, thin in ((top, True), (dark, True), (hidden, False)):
        if len(pts) and thin:
            pts = pts[rng.random(len(pts)) < keep]
        out.append(pts @ R + rng.normal(0., prm.CNN_JITTER, pts.shape) + shift if len(pts) else pts.reshape(0, 2))
    return out[0], out[1], out[2], sample["yaw"] + th


def getBatch(samples, sym180, rng=None):
    """
    Returns (images, symbol labels, angle targets) as tensors; augmented when rng is given.
    """
    images, labels, angles = [], [], []
    for s in samples:
        top, dark, hidden, yaw = augment(s, rng) if rng is not None else (s["top"], s["dark"], s["hidden"], s["yaw"])
        images.append(getInputImage(top, dark, hidden))
        labels.append(s["label"])
        angles.append(getAngleTarget(yaw, sym180[s["label"]]))
    return (torch.from_numpy(np.stack(images)), torch.tensor(labels),
            torch.from_numpy(np.stack(angles).astype(np.float32)))


# ------------------------------------------- 2. VALIDATION AND CALIBRATION -----------------------------------------------

def validate(net, samples, sym180):
    """
    Returns one row per sample: (right symbol and angle, margin, camera kind).
    """
    net.eval()
    rows = []
    with torch.no_grad():
        for i in range(0, len(samples), 256):
            part = samples[i:i + 256]
            images, _, _ = getBatch(part, sym180)
            ls, la = net(images)
            ps, pa = torch.softmax(ls, 1).numpy(), torch.softmax(la, 1).numpy()
            for j, s in enumerate(part):
                k = int(np.argmax(ps[j]))
                margin, b = getMargins(ps[j], pa[j], sym180[k])
                d = abs(wrapAngle(b * 2 * np.pi / prm.CNN_N_ANGLE_BINS - s["yaw"]))
                tol = np.radians(prm.ANGLE_TOLERANCE_DEG)
                angle_ok = d < tol or (sym180[k] and abs(d - np.pi) < tol)
                rows.append((k == s["label"] and angle_ok, margin, s["kind"]))
    net.train()
    return rows


def getMarginThreshold(rows, kind, max_error):
    """
    Returns the lowest margin above which the reads of one camera kind are wrong at most max_error of the time.
    """
    rows = sorted([r for r in rows if r[2] == kind], key=lambda r: -r[1])
    best, wrong = 1., 0
    for i, (ok, m, _) in enumerate(rows):
        wrong += not ok
        if wrong / (i + 1) <= max_error:
            best = m
    return best


def getCalibration(rows):
    """
    Returns the piecewise-linear map from CNN margin to the template confidence scale:
    margin where close reads are wrong <= TARGET_ERROR_CLOSE -> CONF_ACCEPT, far reads <= TARGET_ERROR_FAR -> CONF_ACT,
    half of the accept margin -> CONF_VERIFY.
    """
    m_accept = getMarginThreshold(rows, "close", prm.TARGET_ERROR_CLOSE)
    m_act = max(getMarginThreshold(rows, "far", prm.TARGET_ERROR_FAR), m_accept + 0.01)
    points = sorted({0.: 0., 0.5 * m_accept: prm.CONF_VERIFY, m_accept: prm.CONF_ACCEPT, m_act: prm.CONF_ACT,
                     1.: 1.}.items())
    margins, confs = zip(*points)
    return {"margin": np.array(margins), "conf": np.array(confs)}


# ------------------------------------------- 3. TRAINING -----------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", default=["train_a", "train_b"], help="one or more cnn/data/<name>.npz files")
    ap.add_argument("--epochs", type=int, default=prm.CNN_EPOCHS)
    args = ap.parse_args()

    rng = np.random.default_rng(0)
    torch.manual_seed(0)
    sym180 = loadTemplates(cells=())["sym180"]
    train, val, val_seeds = [], [], []
    for name in args.data:                                              # the last scenes of EVERY file are held out
        samples = loadSamples(name)
        seeds = sorted({s["seed"] for s in samples})
        held = set(seeds[-max(1, int(round(len(seeds) * prm.CNN_VALIDATION_SHARE))):])
        train += [s for s in samples if s["seed"] not in held]
        val += [s for s in samples if s["seed"] in held]
        val_seeds += sorted(held)
    print(f"{len(train)} training blobs, {len(val)} validation blobs (scenes {sorted(val_seeds)})")

    net = Net()
    bs = prm.CNN_BATCH_SIZE
    steps = args.epochs * (len(train) // bs)
    opt = torch.optim.AdamW(net.parameters(), prm.CNN_LEARNING_RATE, weight_decay=prm.CNN_WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, prm.CNN_MAX_LEARNING_RATE, total_steps=steps)
    best = (-1., None)
    for epoch in range(args.epochs):
        order = rng.permutation(len(train))
        total = 0.
        for i in range(len(train) // bs):
            images, labels, angles = getBatch([train[j] for j in order[i * bs:(i + 1) * bs]], sym180, rng)
            ls, la = net(images)
            loss = F.cross_entropy(ls, labels) + F.cross_entropy(la, angles)     # symbol + soft-target angle loss
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            total += loss.item()
        acc = np.mean([r[0] for r in validate(net, val, sym180)])
        print(f"epoch {epoch + 1:2d}: loss {total / max(len(train) // bs, 1):.3f}, "
              f"validation symbol + angle right {100 * acc:.1f} %", flush=True)
        if acc > best[0]:
            best = (acc, {k: v.clone() for k, v in net.state_dict().items()})

    net.load_state_dict(best[1])
    calibration = getCalibration(validate(net, val, sym180))
    print("calibration (margin -> conf):",
          ", ".join(f"{m:.3f}->{c:.2f}" for m, c in zip(calibration["margin"], calibration["conf"])))
    torch.save({"state": net.state_dict(), "calibration": calibration, "validation_accuracy": best[0]},
               prm.CNN_WEIGHTS_FILE)
    print(f"saved {prm.CNN_WEIGHTS_FILE} (validation {100 * best[0]:.1f} %)")
