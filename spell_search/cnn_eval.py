# Compare the learned reader (CNN, cnn.py) with the classical template reader on blobs from scenes that were
# not used for training (cnn_data.py with other seeds).
#
#   python3 spell_search/cnn_eval.py --data data/cnn_test.npz [--max 400] [--json cnn_eval.json]
#
# A read is right if the symbol is right and the yaw is within 10 deg (or 180 deg off for a glyph that looks the
# same after a half turn): only then is the piece placed readable. Reported per camera (mast: far, sparse points;
# wrist: close), for whole pieces and for pieces cut by the image border, and under extra noise
# (5 mm jitter, half of the points dropped) as a robustness check.
import os
import sys
import json
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from world import World, wrap
from perception import Templates, classify_template
from cnn import Classifier

SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def noisy(s, rng):
    out = {}
    for k in ("top", "dark"):
        p = s[k][rng.random(len(s[k])) < .5]
        out[k] = p + rng.normal(0, .005, p.shape)
    return out


def main():
    S = np.load(arg("--data", "data/cnn_test.npz"), allow_pickle=True)["samples"]
    S = [s for s in S if s["label"] >= 0]
    rng = np.random.default_rng(0)
    if len(S) > int(arg("--max", 400)):
        S = list(rng.choice(S, int(arg("--max", 400)), replace=False))
    W = World(seed=0)
    tpl = Templates(W.C, W.pieces, W.symbol)
    cnn = Classifier()
    readers = {"templates": lambda c: classify_template(tpl, c), "CNN": lambda c: cnn(tpl, c)}
    res = []
    for i, s in enumerate(S):
        truth, yaw = SYMBOLS[s["label"]], s["yaw"]
        for cond in ("clean", "noisy"):
            pts = {"top": s["top"], "dark": s["dark"]} if cond == "clean" else noisy(s, rng)
            if len(pts["top"]) < 20:
                continue
            cand = {"top": pts["top"].astype(float), "dark": pts["dark"].astype(float), "stacked": s["stacked"], "z_top": 0.}
            for name, f in readers.items():
                t0 = time.time()
                x = f(cand)
                dt = time.time() - t0
                dy = abs(wrap(x["yaw"] - yaw))
                yaw_ok = dy < np.radians(10) or (tpl.sym180[x["symbol"]] and abs(dy - np.pi) < np.radians(10))
                ok = x["symbol"] == truth and yaw_ok
                res.append({"reader": name, "cond": cond, "kind": s["kind"], "partial": bool(s["partial"]),
                            "ok": bool(ok), "sym_ok": x["symbol"] == truth, "conf": x["conf"], "ms": 1000 * dt})
        if (i + 1) % 50 == 0:
            print(f"{i + 1}/{len(S)} blobs", flush=True)

    def row(sel):
        r = [x for x in res if sel(x)]
        if not r:
            return "-"
        acc = np.mean([x["ok"] for x in r])
        # trusted reads: those the system acts on (wrist: conf >= CONF_ACCEPT); how often are they wrong?
        tr = [x for x in r if x["conf"] >= (CONF_ACCEPT if r[0]["kind"] == "wrist" else CONF_ACT)]
        bad = np.mean([not x["ok"] for x in tr]) if tr else 0.
        return f"{100 * acc:5.1f} % right, {100 * len(tr) / len(r):5.1f} % trusted, {100 * bad:4.1f} % of trusted wrong (n={len(r)})"

    print("\nread right = symbol and yaw right; trusted = conf above the threshold the robot acts on "
          "(wrist: CONF_ACCEPT, mast: CONF_ACT)")
    for cond in ("clean", "noisy"):
        for kind in ("mast", "wrist"):
            for partial in (False, True):
                for name in readers:
                    print(f"{cond:5s} {kind:5s} {'partial' if partial else 'whole  '} {name:9s}: " +
                          row(lambda x: x["reader"] == name and x["cond"] == cond and x["kind"] == kind and x["partial"] == partial))
    for name in readers:
        print(f"time per read, {name}: {np.median([x['ms'] for x in res if x['reader'] == name]):.0f} ms (median)")
    if arg("--json", None):
        with open(arg("--json", None), "w") as f:
            json.dump(res, f)


if __name__ == "__main__":
    main()
