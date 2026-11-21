# Training data for the learned symbol classifier (CNN), generated in simulation: labels are free.
#
# For several random scenes (seeds), a camera is put where the robots would put theirs:
#   - "mast": 1.6 m above a random free floor spot (the coarse read while searching),
#   - "wrist": WRIST_VIEW_H above a random piece (the close re-read before a grasp).
# Every image goes through the same segmentation as the classical reader (perception.segment). A blob is kept
# if one piece explains almost all of its top points; its label is that piece's symbol and yaw (ground truth).
# Blobs of touching pieces are kept too (label -1), so the classifier can be checked on them later.
#
#   python3 spell_search/cnn_data.py --seeds 0-29 --out data/cnn_train.npz
#   python3 spell_search/cnn_data.py --seeds 100-109 --out data/cnn_test.npz     (other scenes for testing)
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from world import World
from perception import Templates, segment, explained
from planning import Planner
import robotic as ry


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def seeds_of(s):
    a, b = (s.split("-") + [s])[:2]
    return range(int(a), int(b) + 1)


def label_blob(W, tpl, cand):
    """(symbol index, yaw, piece) of the piece that explains the blob; label -1: touching / tilted pieces.
    partial: the piece is only partly in view (cut by the image border)"""
    top = cand["top"]
    best = (0., None)
    for n in W.pieces:
        p, yaw = W.piece_pose(n)
        if np.linalg.norm(p[:2] - cand["xy"]) > .25:
            continue
        f = explained(tpl, {"symbol": W.symbol[n], "xy": p[:2], "yaw": yaw}, top, tol=.008).mean()
        if f > best[0]:
            best = (f, n)
    f, n = best
    if n is None or f < .9:
        return -1, np.nan, None, False
    p, yaw = W.piece_pose(n)
    # the whole piece must be in view (pieces at the image border are cut): blob cells / piece cells at 1 cm
    k = tpl.symbols.index(W.symbol[n])
    cells = lambda xy: len(set(map(tuple, np.floor(xy / .01).astype(int))))
    c, s = np.cos(yaw), np.sin(yaw)
    piece = tpl.pts[k] @ np.array([[c, s], [-s, c]]) + p[:2]
    partial = cells(top) < .8 * cells(piece)
    # a piece tilted on another one has a distorted footprint: keep only (almost) flat pieces
    if abs(W.C.getFrame(n).getRotationMatrix()[2, 2]) < .98:
        return -1, np.nan, None, False
    return k, float(yaw), n, partial


def main():
    seeds = seeds_of(arg("--seeds", "0-1"))
    out = arg("--out", "data/cnn_train.npz")
    n_mast, n_wrist = int(arg("--mast", 12)), int(arg("--wrist", 40))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    samples = []
    t0 = time.time()
    for seed in seeds:
        W = World(seed=seed)
        tpl = Templates(W.C, W.pieces, W.symbol)
        P = Planner(W)
        rng = np.random.default_rng(10_000 + seed)
        cam = W.C.addFrame("data_cam")
        exclude = [(c, e + .03) for c, e, _ in P.tables.values()] + \
                  [(W.base_pose(r)[:2], np.array([.42, .42])) for r in ROBOTS]
        free = P.free_grid([])
        mast_z = W.C.getFrame(f"{ROBOTS[0]}_mast").getPosition()[2]
        views = []
        while len([v for v in views if v[0] == "mast"]) < n_mast:
            xy = rng.uniform(P.room[[0, 2]], P.room[[1, 3]])
            if P.is_free(xy, free):
                views.append(("mast", np.r_[xy, mast_z], MAST))
        for n in rng.choice(W.pieces, size=min(n_wrist, len(W.pieces)), replace=False):
            p, _ = W.piece_pose(n)
            off = rng.normal(0, .03, 2)                 # the gripper is never exactly above the piece
            views.append(("wrist", np.r_[p[:2] + off, p[2] + .04 + WRIST_VIEW_H], WRIST))
        for kind, pos, att in views:
            a = rng.uniform(-np.pi, np.pi)              # camera turned about the vertical (any base heading)
            cam.setPosition(pos).setQuaternion([0, np.cos(a / 2), np.sin(a / 2), 0]).setAttributes(att)
            rgb, Pc, valid = W.render("data_cam")
            for cand in segment(Pc, rgb, valid, W.floor_top, exclude):
                if cand["extent"].max() >= .60 or len(cand["top"]) < 40:
                    continue
                k, yaw, n, partial = label_blob(W, tpl, cand)
                c0 = cand["top"].mean(0)
                gt = W.piece_pose(n)[0][:2] - c0 if n is not None else np.array([np.nan, np.nan])
                samples.append(dict(top=(cand["top"] - c0).astype(np.float32), dark=(cand["dark"] - c0).astype(np.float32),
                                    label=k, yaw=yaw, origin=gt.astype(np.float32), kind=kind, seed=seed, partial=partial,
                                    stacked=cand["stacked"]))
        n_ok = sum(s["label"] >= 0 and not s["partial"] for s in samples)
        print(f"seed {seed}: {len(samples)} blobs so far ({n_ok} whole single pieces), {time.time() - t0:.0f} s", flush=True)
    np.savez_compressed(out, samples=np.array(samples, dtype=object), symbols=np.array(tpl.symbols))
    print(f"saved {len(samples)} blobs to {out}")


if __name__ == "__main__":
    main()
