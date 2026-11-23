# perception/cnn/dataset.py

CNN training data from TASK scenes (labels from the truth).

## main (command line: --seeds [0-59], --out, --far, --close)
1. for each seed: samples += getSceneSamples(seed) ; print progress
2. save cnn/data/<out>.npz

## getSceneSamples(seed, n_far, n_close, templates)
1. buildScene(getRandomWord(seed), seed) ; wrist test camera ; truth
2. same views as evaluate.py (getViews)
3. for each blob of each view:
   1. d = describeBlob ; skip if d.underside (black base layer: the reader skips it too)
   2. (k, yaw) = labelDescription(d, truth, label_covered = True)
      -1 when: cut / no single piece explains >= 90 % / tilt > 30 deg / shows < 60 % of the piece's strokes (fragment)
   3. save {top, dark, hidden (minus centre), label, yaw, far|close, cut, occluded, seed}
