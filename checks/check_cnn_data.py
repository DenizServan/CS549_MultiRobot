"""
CHECK the CNN's training data, its saved calibration, and (optionally) what it confuses. No simulator needed.

    python3 checks/check_cnn_data.py --data train_a train_b            what is in the training files
    python3 checks/check_cnn_data.py --data train --confusion test      + accuracy and top confusions on test.npz
        (make test.npz first: python3 perception/cnn/dataset.py --seeds 100-103 --out test)

Prints: blobs per file, how many are usable for training (labelled and not cut), far/close and covered shares, and
the examples per symbol (a symbol with few examples will be read worse). Shows 16 random training images as the
network sees them (red outline, green marks, blue hidden) with their label: the label must match the picture and the
letter must be turned by the printed yaw.
Then the calibration stored in cnn_weights.pt: the margin -> confidence points. CONF_VERIFY / CONF_ACCEPT / CONF_ACT
were fixed to the values in parameters.py AT TRAINING TIME; changing them later does not change this mapping.
"""
import os
import sys
import argparse
import zipfile
import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "perception"))
sys.path.insert(0, os.path.join(ROOT, "perception", "cnn"))
import parameters as prm
from model import getInputImage

ap = argparse.ArgumentParser()
ap.add_argument("--data", nargs="+", default=["train"])
ap.add_argument("--confusion", default=None, metavar="NAME", help="run the trained CNN on cnn/data/NAME.npz")
args = ap.parse_args()


def load(name):
    return list(np.load(os.path.join(prm.CNN_DATA_DIR, name + ".npz"), allow_pickle=True)["samples"])


usable_all = []
for name in args.data:
    S = load(name)
    usable = [s for s in S if s["label"] >= 0 and not s["cut"]]
    usable_all += usable
    print(f"{name}: {len(S)} blobs, {len(usable)} usable for training (labelled, not cut); "
          f"cut {sum(bool(s['cut']) for s in S)}, unlabelled {sum(s['label'] < 0 for s in S)}; "
          f"of the usable: far {sum(s['kind'] == 'far' for s in usable)}, close {sum(s['kind'] == 'close' for s in usable)}, "
          f"covered {sum(bool(s['occluded']) for s in usable)}; scenes {len({s['seed'] for s in S})}")

counts = np.bincount([s["label"] for s in usable_all], minlength=prm.N_SYMBOLS)
print("\nexamples per symbol:", " ".join(f"{c}:{n}" for c, n in zip(prm.SYMBOLS, counts)))
print("fewest:", ", ".join(f"{c}:{n}" for n, c in sorted(zip(counts.tolist(), prm.SYMBOLS))[:5]))

rng = np.random.default_rng(0)
fig, axes = plt.subplots(4, 4, figsize=(10, 10))
for ax, j in zip(axes.ravel(), rng.choice(len(usable_all), size=min(16, len(usable_all)), replace=False)):
    s = usable_all[j]
    img = getInputImage(s["top"], s["dark"], s.get("hidden", np.zeros((0, 2))))
    ax.imshow(np.dstack([img[0], img[1], img[2]]), origin="lower")
    ax.set_title(f"{prm.SYMBOLS[s['label']]} yaw {np.degrees(s['yaw']):.0f}° {s['kind']}"
                 + (" cov" if s["occluded"] else ""), fontsize=8)
    ax.axis("off")
plt.tight_layout()

# calibration (read without torch: the pickle inside the .pt zip, tensors skipped)
import pickle, io


class _NoTorch(pickle.Unpickler):
    def find_class(self, mod, n):
        return (lambda *a, **k: None) if mod.startswith("torch") else super().find_class(mod, n)

    def persistent_load(self, pid):
        return None


z = zipfile.ZipFile(prm.CNN_WEIGHTS_FILE)
saved = _NoTorch(io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith("data.pkl"))))).load()
cal = saved["calibration"]
print(f"\ncnn_weights.pt: validation accuracy {100 * saved['validation_accuracy']:.1f} % "
      "(best epoch chosen on this same validation set, and the calibration fitted on it: optimistic)")
print("calibration margin -> conf:", ", ".join(f"{m:.3f}->{c:.2f}" for m, c in zip(cal["margin"], cal["conf"])))
print(f"parameters.py now: CONF_VERIFY {prm.CONF_VERIFY}, CONF_ACCEPT {prm.CONF_ACCEPT}, CONF_ACT {prm.CONF_ACT}")

if args.confusion:
    import torch
    from classify_cnn import CnnClassifier
    net = CnnClassifier()
    S = [s for s in load(args.confusion) if s["label"] >= 0 and not s["cut"]]
    pairs, right = {}, 0
    for s in S:
        img = getInputImage(s["top"], s["dark"], s.get("hidden", np.zeros((0, 2))))
        with torch.no_grad():
            ls, _ = net.net(torch.from_numpy(img[None, :net.n_layers]))
        k = int(ls.argmax())
        right += k == s["label"]
        if k != s["label"]:
            key = (prm.SYMBOLS[s["label"]], prm.SYMBOLS[k])
            pairs[key] = pairs.get(key, 0) + 1
    print(f"\n{args.confusion}: symbol right {100 * right / max(len(S), 1):.1f} % of {len(S)} labelled whole blobs "
          "(symbol only; evaluate.py also checks the angle and the confidence)")
    print("top confusions (true -> read: count):",
          ", ".join(f"{a}->{b}: {n}" for (a, b), n in sorted(pairs.items(), key=lambda t: -t[1])[:12]))
plt.show()
