# spell_search: two mobile Pandas search a room and spell a sentence

Two mobile manipulators (Franka Panda arms on `transXYPhi` bases) search a room for letter- and digit-shaped pieces. They assemble a target sentence on their tables:

- the first word goes on `table_left`, built by `p1`;
- the second word goes on `table_right`, built by `p2`.

The scene is the one from `place_characters.py`: `N_PIECES` letter and digit pieces (72 by default, every character at least once), randomly placed in the room and settled with PhysX.

## How it maps to the proposal and the feedback

| Proposal / feedback | Here |
|---|---|
| Symbol perception (template baseline) | `perception.py`: depth → point cloud → pieces → template matching over 36 symbols × 72 rotations, using the stroke boxes and bottom marks from `characters.g` |
| **Feedback: re-read every piece with the wrist camera (core, not stretch)** | `agents.py: fetch()`: before each grasp the gripper moves above the piece and the wrist camera re-reads it. The grasp uses the refined pose. A wrong or unsure read is rejected and the map is corrected. Use `--no-reread` for the ablation. |
| **Feedback: use detection actively** | Every mast read goes into a shared map with its confidence and runner-up symbols. A robot picks its next piece in this order (`coordination.reserve_piece`): (1) a confident read of a symbol it needs; (2) an unsure read, checked close up with the wrist camera; (3) once the room is searched, a piece where a needed symbol was the runner-up; (4) a blob that could not be read from far (touching pieces). Wrist close-ups correct the map for every piece in view. Touching pieces are separated by explaining away the best-fitting template and reading the rest again. |
| **Feedback: search for the pieces together, without colliding** | `coordination.py`: shared map, viewpoint claiming (the robots spread out), piece reservation, the other robot's pose and goal as path obstacles, stop-if-too-close while driving, and a workspace lock for the arms |
| Shared-zone scheduler, piece reservation, collision checks | `coordination.py` (`Blackboard`, `Traffic`) |
| KOMO, shape grasps, joint-7 limits | `planning.py`: IK with KOMO (collisions, joint limits). The grasp is the `_grasp` marker of the piece; both closing directions are tried, so the wrist rotation stays within joint limits. |
| Upright placement | Pieces are placed so that they read upright from the front of the tables (looking +x). |
| Metrics | Sentence accuracy (symbol, cell, upright), time, distances, waits, re-read rejections, misreads caught, grasp failures, minimum distance between the bases |
| Clearing the way (guideline: manipulate surrounding objects to reach the targets) | `agents.py: go(), clear_way(), set_aside()`: the pieces on the floor are obstacles in a shared occupancy grid built from the mast depth image (updated while driving). If every path drives over pieces, the first one is picked up: needed by this robot → to its table; otherwise → put down within reach, off the path, and kept on the shared map. A robot holding a piece puts it down, clears, and picks it up again. `--no-clear` for the ablation. |
| Collision checks (ground truth) | `safety.py`: a separate copy of the scene in which the pieces collide, checked at 10 Hz: robot–robot, robot–table/wall, arm–piece, held piece, base–piece contact episodes and the deepest penetration |

## Install (Ubuntu 22.04, or WSL2 on Windows)

RAI (`robotic`) runs only on Linux, so on Windows use WSL2. The viewer works through WSLg.

```bash
sudo apt install -y python3-venv libglu1-mesa liblapack3 ffmpeg     # ffmpeg only for --video
python3 -m venv ~/venvs/rai
source ~/venvs/rai/bin/activate
pip install -r requirements.txt          # robotic==0.4.1 numpy scipy pillow
```

## Run

From the `CS449_Project_ws` folder (on Windows/WSL: `cd "/mnt/c/DESKTOP/Engineering/BSC_MSC_PHD/BİLKENT_DOKTORA/CS 549 - Learning for Robotics/Project/CS449_Project_ws"`):

```bash
python3 config_test.py                                   # only the scene
python3 place_characters.py                              # scene + scattered characters
python3 spell_search/run.py                              # the whole task, live viewer
python3 spell_search/run.py --seed 3 --sentence "AB12 XY9"
python3 spell_search/run.py --headless --json out.json   # no viewer, metrics to a file
python3 spell_search/run.py --headless --no-reread       # ablation: no wrist re-read
python3 spell_search/run.py --headless --video vid       # vid/run.mp4 (overview camera, 4x real time; frames go straight into ffmpeg)
python3 spell_search/run.py --headless --no-monitor      # skip the ground-truth collision monitor
python3 spell_search/run.py --headless --no-clear        # ablation: bases drive over pieces instead of clearing the way
```

- Without clearing (`--no-clear`) a run takes a few minutes of wall time. With clearing it takes longer; a run stops at the latest after `MAX_TIME` = 1800 s of simulated time (`--time` changes it). Most of the wall time goes to perception.
- On a machine without a display (a server, or WSL without WSLg), prefix the command with `xvfb-run -a`. The cameras need an OpenGL context.

## Files

| File | What |
|---|---|
| `config.py` | all parameters |
| `world.py` | builds the scene (via `../place_characters.py`), adds mast and wrist cameras, moves bases and arms, attaches and detaches pieces, renders cameras, checks whether a grasp holds |
| `perception.py` | segmentation and template matching, confidence |
| `planning.py` | KOMO IK, collision-checked joint paths, A* base navigation, base poses for pick and place |
| `coordination.py` | shared map and reservations (`Blackboard`), traffic and workspace lock (`Traffic`) |
| `agents.py` | one robot's behaviour (search → fetch with re-read → deliver), as a generator |
| `run.py` | main loop, evaluation, metrics, video |
| `safety.py` | ground-truth collision monitor (evaluation only, the robots never read it) |

## Simplifications (to be replaced later)

- **Kinematic execution.** Joints follow the plans exactly, and a grasped piece is rigidly attached to the gripper. A grasp only succeeds if the fingers close across a stroke (`world.grasped_piece`). Perception and grasp errors carry into the final placement, because the piece is released where it actually is in the hand.
- **No physical contact with the floor.** Pieces are never pushed. With clearing on, bases avoid or clear pieces; when that is impossible (a piece that cannot be grasped, or too many nested clearings) they drive over it, and the run counts it (`drove_over`, and `base_piece` in the collision monitor).
- **Clutter vs. time.** `N_PIECES` in `config.py` sets the density (every character at least once, the rest random extra copies; a symbol the sentence repeats always has enough copies). With the 0.75 m corridor (`CLEARANCE`), the largest connected free area is 54 % of the room with 37 pieces, 35 % with 72 (default) and 25 % with 90 (76 % without pieces).
- **Cluttered pieces.** A piece lying on or tightly against others can stay unreadable, even close up; clearing moves pieces out of the way of the base, not off another piece, so such a cell can stay empty until the timeout.
- **Learned reader not yet the default.** The CNN (`--cnn`, see below) reads isolated pieces as well as the templates, 10x faster, but in the full task it still sends the robots to check too many reads (tuning of `CONF_*` / the search tiers for the CNN is open). The VLM baseline is still missing.
- **Mast camera.** It is an idealised camera 1.6 m above each base.

## Learned symbol reader (CNN)

`cnn.py` replaces the template search over 36 symbols x 72 rotations with a small CNN. It plugs into
`perception.classify` (via `perception.CLASSIFIER`), returns the same dict, and is switched on with `--cnn`.

| | |
|---|---|
| Input | the blob from `perception.segment` as a 2-channel top view: stroke points, dark bottom marks (64 x 64, 5 mm/pixel) |
| Output | p(symbol) over 36 and p(yaw) over 72 bins of 5 deg; the winner's pose is refined by the classical fine fit (1 deg, 5 mm) |
| Replaces | the exhaustive template correlation that decides symbol and coarse yaw |
| Keeps | segmentation, the fine pose fit, the touching-piece test, and the fit score as a check on the CNN's confidence |
| Assumes | pieces look like the simulated ones (trained on rendered views only) |
| Confidence | margin (best minus runner-up, for symbol and for upside-down yaw), mapped onto the template scale on held-out scenes, so `CONF_ACT` / `CONF_VERIFY` / `CONF_ACCEPT` keep their meaning; then scaled down when the template of the answer fits badly (pieces cut by the image border) |

### Files

| File | What |
|---|---|
| `cnn.py` | model, rasterisation, `Classifier` (drop-in for `perception.classify`) |
| `cnn_data.py` | training data: random scenes, mast-like and wrist-like views, segmented blobs labelled from the ground truth |
| `cnn_train.py` | training with rotation / point-dropout / jitter augmentation, confidence calibration, writes `cnn_weights.pt` |
| `cnn_eval.py` | CNN vs templates on blobs from unseen scenes (clean and with extra noise) |
| `cnn_weights.pt` | trained weights (20 training scenes, 99 % symbol + yaw on held-out scenes) |

### Run

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu      # once (CPU build is enough)
python3 spell_search/run.py --cnn                                      # full task with the CNN reader
# retrain from scratch (optional, ~15 min data + ~10 min training on a laptop CPU):
python3 spell_search/cnn_data.py --seeds 0-19 --out data/cnn_train.npz
python3 spell_search/cnn_data.py --seeds 100-107 --out data/cnn_test.npz
python3 spell_search/cnn_train.py --data data/cnn_train.npz
python3 spell_search/cnn_eval.py --data data/cnn_test.npz
```

### First results (`cnn_eval.py`, 300 blobs from 8 unseen scenes)

"Right" = symbol right and yaw within 10 deg (180 deg for glyphs that look the same turned). "Trusted wrong" = reads
the robot would act on (conf above `CONF_ACT` for the mast, `CONF_ACCEPT` for the wrist) that are wrong: these are the
dangerous ones. "Noisy" = 5 mm jitter and half of the points dropped.

| Camera, piece | Templates: right / trusted wrong | CNN: right / trusted wrong |
|---|---|---|
| mast, whole, clean | 97.6 % / 0.0 % | 97.6 % / 0.0 % |
| mast, whole, noisy | 86.7 % / 4.7 % | **96.4 % / 0.0 %** |
| wrist, whole, clean | **100 %** / 0.0 % | 97.5 % / 0.0 % |
| wrist, whole, noisy | **100 %** / 0.0 % | 93.8 % / 0.0 % |
| wrist, cut by the border | 6.8 % / 76.9 % | 4.5 % / **33.3 %** (trusted 6.8 % of the time vs 29.5 %) |
| time per read | 229 ms | **22 ms** |

Without the fit check the CNN trusted 75 % of the reads of cut pieces at the wrist, 94 % of them wrong; the fit check
brought that to 6.8 %. Open: the full task with `--cnn` is still slower than with templates (more wrist rejections of
mast reads), a multi-seed benchmark, and the VLM baseline.
