# perception/

Reads the letter/digit pieces on the floor: camera picture in, list of (symbol, position, angle, confidence) out.
One file per pipeline step; every number lives in `parameters.py`; only `ground_truth.py`, `evaluate.py` and
`cnn/dataset.py` may look at the true piece poses.

| Step | File | In | Out |
|---|---|---|---|
| 0 | `parameters.py` | | all constants |
| 1 | `scene_builder.py` | word, seed | THE task scene: every symbol once + the word's letters twice more, 30 % in piles, the rest scattered (some near walls), settled; cameras |
| 2 | `camera.py` | camera name | point cloud in room coordinates (+ colours, valid mask) |
| 3 | `segmentation.py` | point cloud | blobs: one per visible surface (depth jumps split stacked pieces), with cut / covered flags |
| 4 | `blob.py` | blob | top face found by a plane fit, laid flat: outline + black bottom marks (2-D), tilt |
| 5 | `templates.py` | `characters.g` | the 36 letter models as grids |
| 6a | `classify_template.py` | description | symbol, coarse angle, margin (template matching) |
| 6b | `cnn/classify_cnn.py` | description | the same, from the CNN |
| 7 | `refine.py` | description + answer | exact angle, piece origin, fit checks |
| 8 | `confidence.py` | scores, fit checks | one confidence number |
| 9 | `reader.py` | camera name | list of reads (runs steps 2-8, splits touching pieces) |
| - | `ground_truth.py` | scene | true symbols and poses (evaluation only) |
| - | `evaluate.py` | seeds | accuracy tables per piece kind (whole / near wall / stacked / tilted / cut / covered), measured thresholds |
| - | `robot_test.py` | seed, reader | one robot reads, drives, re-reads, grasps at the read pose, unstacks piles and turns pieces upright (viewer) |
| - | `robot_run.py` | team repo path | the team's full two-robot task with this reader plugged in (slow) |
| - | `cnn/model.py`, `cnn/dataset.py`, `cnn/train.py` | | CNN network, training data, training |

Run from the repository folder (on a machine without a display, prefix with `xvfb-run -a`):

```bash
python3 perception/scene_builder.py                 # look at the task scene (word ROBOTICS)
python3 perception/scene_builder.py HELLO           # ... for another word
python3 perception/templates.py                     # look at the 36 templates
python3 perception/reader.py                        # read one test-camera picture
python3 perception/cnn/dataset.py --seeds 0-29 --out train_a               # CNN training data, task scenes (~8 min)
python3 perception/cnn/dataset.py --seeds 30-59 --out train_b              # (two halves can run in parallel)
python3 perception/cnn/train.py --data train_a train_b                     # train (~30-50 min on a laptop CPU)
python3 perception/evaluate.py --reader cnn --seeds 80-89                  # measure thresholds (calibration seeds)
python3 perception/evaluate.py --reader cnn --seeds 100-109                # final numbers (test seeds)
python3 perception/robot_test.py --reader cnn --seed 0 --targets 10        # watch perception in the scene
```

The thresholds the robots act on are per reader, in `motion/motion_parameters.py` (`READER_THRESHOLDS`): copy the
values `evaluate.py --seeds 80-89` prints there after retraining. `CONF_ACT / CONF_VERIFY / CONF_ACCEPT` in
`parameters.py` are only the scale the CNN calibration is mapped onto during training (and the defaults).

## Calibration on the task scene (2026-11-22)

Everything is tuned for one task: `scene_builder.buildScene` (52-56 pieces; 30 % in 3 tight piles, the rest scattered,
a quarter of those within 0.4 m of a wall). CNN trained on seeds 0-59 (5,517 labelled blobs, validation 94.5 %),
thresholds measured on seeds 80-89, numbers below on seeds 100-109 (never used before), CNN reader with
READER_THRESHOLDS["cnn"] = (0.02, 0.01, 0.02):

| camera | piece | right | trusted | trusted wrong |
|---|---|---|---|---|
| far (mast) | whole, open floor | 95.5 % | 90.6 % | 0.6 % |
| far (mast) | near a wall | 95.5 % | 92.1 % | 0.0 % |
| far (mast) | tilted (piles) | 75.0 % | 18.8 % | 0.0 % |
| far (mast) | all reads | | | 0.4 % (2 of 450) |
| close (wrist) | whole, open floor | 87.0 % | 86.0 % | 0.0 % |
| close (wrist) | near a wall | 98.6 % | 95.9 % | 0.0 % |
| close (wrist) | stacked (flat on a pile) | 55.2 % | 55.2 % | 0.0 % |
| close (wrist) | tilted (piles) | 55.0 % | 9.4 % | 0.0 % |
| close (wrist) | all reads | | | 0.0 % (0 of 273) |

What changed in the calibration and why:
- `MAX_TILT_DEG` 35 -> 15: trusted reads of pieces tilted 15-35 deg were wrong 5-6 % of the time. Such pieces lie on
  piles; the robots spread them (put them down flat) and read them there instead.
- Black base layers (seen beside tilted pieces, or a piece upside down) are skipped (`blob.py` "underside").
- Training labels need at least 60 % of the piece visible (fragments were labelled before and taught the CNN noise).
- The template fit check (`confidence.fitPenalty`) now applies to BOTH readers: fragments fit simple glyphs (L, J, 1)
  with a large margin, and the template reader trusted those 10-20 % wrong.
- The template reader stays the weaker fallback: READER_THRESHOLDS["template"] = (0.15, 0.075, 0.15) trusts about 53 %
  (far) / 66 % (close) of whole pieces at about 2 % / 1 % wrong on the test seeds.
- Compared with the CNN shipped before (both with the 15 deg tilt rule), the retrained CNN trusts about as many whole
  pieces and makes fewer trusted mistakes (far 2 vs 3, close 0 vs 1 on the test seeds); it reads covered and tilted
  blobs much better (validation 94.5 % vs 66.5 %), but the robots do not trust those anyway.
