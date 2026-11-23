"""
Training data for the CNN reader, generated in simulation (labels come free from the ground truth).

    python3 perception/cnn/dataset.py --seeds 0-39 --out train        ->  cnn/data/train.npz
    python3 perception/cnn/dataset.py --seeds 100-103 --out test      ->  cnn/data/test.npz
    python3 perception/cnn/train.py --data train

Every seed builds the task scene (scene_builder.buildScene) for a random word (evaluate.getRandomWord), and the same
far and close views as evaluate.py are taken; every blob goes through the normal pipeline (camera -> segmentation ->
description) and is labelled with the true piece that explains it (label -1 when no single piece does: touching
pieces, or tilted more than LABEL_MAX_TILT_DEG). Covered pieces ARE labelled (the CNN gets the hidden region as an
input layer and learns to read them). Saved per blob: outline, mark and hidden points relative to the blob centre,
label, true yaw, camera kind (far/close), cut and occluded flags, and seed.
"""
import os
import sys
import argparse
import numpy as np
import robotic as ry #type: ignore

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # perception/
import parameters as prm
from scene_builder import buildScene
from camera import takePicture, getIgnoreBoxes
from segmentation import getBlobs
from blob import describeBlob
from templates import loadTemplates
from ground_truth import getTruth, labelDescription
from evaluate import addWristTestCamera, placeCamera, getViews, parseSeeds, getRandomWord


def getSceneSamples(seed, n_far, n_close, templates):
    """
    Returns the labelled blobs of every view of one task scene (random word for the seed).
    """
    C, names, floor_z, _ = buildScene(getRandomWord(seed), seed=seed, cameras=("test",), verbose=False)
    addWristTestCamera(C)
    view = ry.CameraView(C)
    truth = getTruth(C, names)
    samples = []
    for kind, cam, xy, z, heading in getViews(C, truth, floor_z, seed, n_far, n_close):
        placeCamera(C, cam, xy, z, heading)
        rgb, points, valid, size = takePicture(view, C, cam)
        blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C), floor_z)
        for blob in blobs:
            d = describeBlob(blob, floor_z, blobs)
            if d["underside"]:                              # the reader skips these too
                continue
            k, yaw = labelDescription(d, truth, templates, label_covered=True)
            samples.append({"top": (d["top"] - d["centre"]).astype(np.float32),
                            "dark": (d["dark"] - d["centre"]).astype(np.float32),
                            "hidden": (d["hidden"] - d["centre"]).astype(np.float32),
                            "label": k, "yaw": yaw, "kind": kind, "cut": d["cut"], "occluded": d["occluded"],
                            "seed": seed})
    return samples


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default=f"{prm.TUNING_SEEDS[0]}-{prm.TUNING_SEEDS[-1]}")
    ap.add_argument("--out", default="train")
    ap.add_argument("--far", type=int, default=prm.FAR_VIEWS_PER_SCENE)
    ap.add_argument("--close", type=int, default=prm.CLOSE_VIEWS_PER_SCENE)
    args = ap.parse_args()

    templates = loadTemplates()
    samples = []
    for seed in parseSeeds(args.seeds):
        samples += getSceneSamples(seed, args.far, args.close, templates)
        n_ok = sum(s["label"] >= 0 and not s["cut"] for s in samples)
        print(f"seed {seed}: {len(samples)} blobs so far ({n_ok} labelled whole pieces)", flush=True)
    os.makedirs(prm.CNN_DATA_DIR, exist_ok=True)
    path = os.path.join(prm.CNN_DATA_DIR, args.out + ".npz")
    np.savez_compressed(path, samples=np.array(samples, dtype=object))
    print(f"saved {len(samples)} blobs to {path}")
