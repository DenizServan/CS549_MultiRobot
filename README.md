# CS549 Multi-Robot: two robots spell a word

Two Franka Panda arms on mobile bases read the letter and digit pieces scattered and piled on the floor, fetch the
ones they need and spell a word on their tables: p1 puts the first half on `table_left`, p2 the second half on
`table_right`. Built on RAI (`robotic`) with PhysX. CS449/549 Learning for Robotics, Bilkent University, Fall 2026.
The proposal is `Csprop.pdf`.

## Install (once; Ubuntu 22.04, or WSL2 on Windows)

```bash
sudo apt install -y python3-venv libglu1-mesa liblapack3 ffmpeg git-lfs
git lfs install
git clone https://github.com/DenizServan/CS549_MultiRobot.git      # git-lfs fetches the CNN weights
cd CS549_MultiRobot
python3 -m venv ~/venvs/rai
source ~/venvs/rai/bin/activate
pip install -r requirements.txt
```

The trained CNN (`perception/cnn/cnn_weights.pt`) is stored with Git LFS (`.gitattributes` tracks `*.pt`). If it
was cloned without git-lfs, the file is a small text pointer: run `git lfs pull` in the repository folder.

## Run (from the repository folder)

```bash
source ~/venvs/rai/bin/activate

python3 config_test.py                                  # the empty scene
python3 motion/spell.py                                 # the whole task: CNN reader, seed 0, word "ROBOTICS", viewer
python3 motion/spell.py --word "HELLO" --seed 1
python3 motion/spell.py --reader template --headless    # template reader, no viewer

python3 perception/scene_builder.py                     # look at the task scene
python3 perception/reader.py                            # read one test-camera picture
python3 perception/robot_test.py --reader cnn --seed 0 --targets 10    # one robot: read, re-read, grasp, unstack
python3 perception/evaluate.py --reader cnn --seeds 100-109            # reading accuracy on test seeds

python3 checks/check_segmentation.py                    # one check script per step (see checks/)
```

Train the CNN again (data goes to `perception/cnn/data/`, which is not in the repository):

```bash
python3 perception/cnn/dataset.py --seeds 0-29 --out train_a      # training data from task scenes (~8 min)
python3 perception/cnn/dataset.py --seeds 30-59 --out train_b
python3 perception/cnn/train.py --data train_a train_b            # ~30-50 min on a laptop CPU
python3 perception/evaluate.py --reader cnn --seeds 80-89         # measure the thresholds, then copy them into
                                                                  # motion/motion_parameters.py (READER_THRESHOLDS)
```

On a machine without a display, prefix commands with `xvfb-run -a` (the cameras need OpenGL).

## Code

| Folder | What |
|---|---|
| `perception/` | camera picture in, list of (symbol, position, angle, confidence) out: scene, point cloud, segmentation, blobs, template and CNN readers, refinement, confidence, evaluation. Constants in `parameters.py`. |
| `motion/` | both robots at the same time: arm (KOMO IK), base (A*), clearance between the robots, shared piece map, pick, spread a pile, grasp from geometry, place upright, score, and `spell.py` that runs it all. Constants in `motion_parameters.py`. |
| `checks/` | one script per pipeline step, to look at what each step does |
| `pseudocode/` | every script walked through step by step |
| `graph_files/` | the room, tables, Panda models and the 36 letter pieces |

Details and the measured reading accuracy: `perception/README.md`, `motion/README.md`, `pseudocode/README.md`.

`perception/robot_run.py` plugs the reader into the team's earlier two-robot code (`spell_search/`), which is no
longer in this branch: it is in the history (commit `227df62`), pass its folder with `--team`.
