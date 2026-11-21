# CS549 Multi-Robot: two mobile Pandas spell a sentence

Two Franka Panda arms on mobile bases search a room for letter- and digit-shaped pieces and spell a two-word goal
on their tables: the first word on `table_left` (robot `p1`), the second on `table_right` (robot `p2`). Built on
RAI (`robotic`) with PhysX. CS449/549 Learning for Robotics, Bilkent University, Fall 2026.

## Install (once; Ubuntu 22.04, or WSL2 on Windows)

```bash
sudo apt install -y python3-venv libglu1-mesa liblapack3 ffmpeg
python3 -m venv ~/venvs/rai
source ~/venvs/rai/bin/activate
git clone https://github.com/DenizServan/CS549_MultiRobot.git
cd CS549_MultiRobot
pip install -r requirements.txt          # robotic, numpy, scipy, pillow, torch (CPU build is enough)
```

## Run (every time, from the repository folder)

```bash
source ~/venvs/rai/bin/activate
cd CS549_MultiRobot

python3 config_test.py                                    # only the empty scene
python3 place_characters.py                               # scene + scattered pieces
python3 spell_search/run.py                               # the whole task, live viewer (72 pieces, clearing on)
python3 spell_search/run.py --cnn                         # with the learned (CNN) symbol reader
python3 spell_search/run.py --seed 1 --sentence "AB12 XY3"
python3 spell_search/run.py --headless --video out --json out.json     # out/run.mp4 + metrics
python3 spell_search/run.py --headless --no-clear --json noclear.json  # comparison: bases drive over pieces
python3 spell_search/run.py --headless --no-reread        # no wrist-camera re-read before grasping
python3 spell_search/run.py --time 600                    # time limit in simulated seconds (default 1800)
python3 spell_search/run.py --no-monitor                  # skip the collision monitor (faster)
```

Several goals in a row, with videos (see below):

```bash
python3 spell_search/multiple_run.py --cnn                                   # 3 goals: CS549 2026, then word pairs
python3 spell_search/multiple_run.py --cnn --sentences "RAI ARM,CS549 2026"  # your goals first
python3 spell_search/multiple_run.py --cnn --rounds 5 --time 900             # 5 goals, 900 simulated s each
python3 spell_search/multiple_run.py --cnn --headless --video vid            # vid/multiple_run_condensed.mp4
```

Settings are in `spell_search/config.py`:

- `N_PIECES`: piece density; 37 sparse, 72 default, 90 very dense.
- `CLEARANCE`: corridor factor; at 1.5 a 0.5 m base needs a 0.75 m free corridor.
- `SENTENCE`, `SEED`, `MAX_TIME`.

Notes:
- On a machine without a display, prefix commands with `xvfb-run -a`: the robots' cameras need OpenGL.
- WSL with an old Mesa (Ubuntu 20.04): if the viewer crashes with `GLSL 3.30 is not supported` or stays blank,
  `export LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=3.3 MESA_GLSL_VERSION_OVERRIDE=330`.
- The simulation is not paced to real time: it runs as fast as the computer allows, so the viewer moves quickly
  while driving and pauses while the robots read pieces or plan.

## Multiple goals: `multiple_run.py`

1. The goal is written on the wall behind the tables (raised to 2 m in this mode), stroke by stroke.
2. The robots spell it, using the normal task code unchanged (including a finished robot helping the other).
3. Goal reached: confetti, the spelled pieces vanish, the wall is painted over and the next goal is written.
   Goal not reached within `--time`: the goal is struck through in red and the spelled pieces are taken away
   without confetti; then the next goal (or the end, with `--on-timeout stop`).

No pieces are added between goals: a goal is only chosen if the pieces left in the room can spell it. Between
goals, `new_goal()` gives the shared map the new words and keeps what the robots know about the pieces still on the
floor. Details: `spell_search/README_multiple_run.md`.

## Videos: `video.py`

With `--video vid`, `multiple_run.py` writes:

- `vid/multiple_run.mp4`: the overview camera at 4x real time, one frame every 0.2 simulated seconds, and
  `vid/multiple_run.timeline.json`: the simulated time and caption of each frame, and the "slow" windows.
- `vid/multiple_run_condensed.mp4`, made from them when the run ends: routine work at 60x real time, the moments
  that matter at 2x (the 6 s before every placement, a goal being written, reached or struck through), with a
  caption that says what is happening and how fast it plays.

How it works: each raw frame stands for 0.2 simulated seconds and gets a speed (60x, or 2x inside a slow window).
At speed v it lasts 0.2 / v seconds in the condensed video, so at 30 fps a slow frame is shown several times and
most fast frames are skipped. The caption is drawn on each frame with PIL and the frames are encoded by ffmpeg.

```bash
python3 spell_search/video.py vid/multiple_run.mp4 --fast 30 --slow 4         # other speeds, no new simulation
python3 spell_search/run.py --headless --video vid --json vid/run.json        # a run.py video ...
python3 spell_search/video.py vid/run.mp4 --events vid/run.json               # ... condensed with its placements
```

## How the code works

The simulation advances in steps of 50 ms. In each step, each robot's behaviour takes one step, the traffic rules
are updated, and the world ticks (viewer, video, collision monitor). Each robot loops:

1. **Fetch** if the shared map has a piece its table needs: reserve it, drive next to it, re-read it close up with
   the wrist camera (a wrong or unsure read is rejected and the map corrected), grasp it, drive to the table and
   place it upright.
2. **Search** otherwise: drive to the nearest free viewpoint (away from the other robot), read every piece the
   mast camera sees, and add the reads to the shared map.
3. **Help** when its own word is done: fetch the pieces the other table still needs.

Pieces on the floor are obstacles. When every path is blocked, the robot clears the way: it picks up the piece in
the way and takes it to its table if it needs it, otherwise it puts it down off the path.

| File (in `spell_search/`) | Role |
|---|---|
| `config.py` | all parameters |
| `world.py` | the scene (built by `../place_characters.py`), mast and wrist cameras, moving bases and arms, attaching pieces |
| `perception.py` | depth image → point cloud → blobs → symbol, rotation, position and confidence (template matching) |
| `cnn.py` | the learned reader: a small CNN that replaces the template search (`--cnn`); `cnn_data.py`, `cnn_train.py`, `cnn_eval.py` make and test it |
| `planning.py` | arm IK with KOMO, collision-checked arm motions, A* paths for the bases, poses for picking, placing and setting pieces aside |
| `coordination.py` | the shared map (`Blackboard`): who saw which piece where, reservations, target cells; `Traffic`: distance rules and the shared-workspace lock |
| `agents.py` | one robot's behaviour (search → fetch → deliver → help), written as a Python generator: one `yield` is one 50 ms step |
| `run.py` | one goal: builds everything, runs the loop, scores the tables (right symbol, right cell, upright), prints metrics |
| `safety.py` | collision monitor for evaluation only (the robots never read it) |
| `multiple_run.py` | several goals in a row, the wall text and effects, `new_goal()` |
| `video.py` | the raw and condensed videos |

Simplifications: the arms follow their plans exactly, and a grasped piece is attached rigidly to the gripper. A
grasp only succeeds if the fingers close across a stroke. Physics (PhysX) is used to scatter and settle the pieces
at the start. More in `spell_search/README.md`.
