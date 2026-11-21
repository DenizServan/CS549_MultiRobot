# Multiple goals in a row, and videos

Two new files; the rest of the code is unchanged.

| File | What |
|---|---|
| `multiple_run.py` | several goals in a row. Uses `world.py`, `coordination.py`, `agents.py` and the helpers of `run.py` as they are. |
| `video.py` | a raw video plus a condensed one: routine work plays at 60x, the moments that matter at 2x, with a caption. |

## Run (from the `CS449_Project_ws` folder)

```bash
python3 spell_search/multiple_run.py --cnn                                   # 3 goals: CS549 2026, then word pairs
python3 spell_search/multiple_run.py --cnn --sentences "RAI ARM,CS549 2026"  # your goals first, then word pairs
python3 spell_search/multiple_run.py --cnn --rounds 5 --time 900             # 5 goals, 900 simulated s each
python3 spell_search/multiple_run.py --cnn --headless --video vid            # vid/multiple_run.mp4 + vid/multiple_run_condensed.mp4
python3 spell_search/multiple_run.py --cnn --rounds 1 --video vid            # one goal, with the condensed video
python3 spell_search/multiple_run.py --on-timeout stop                       # end when a goal is not reached
```

Also as in `run.py`: `--seed`, `--headless`, `--no-reread`, `--no-clear`. `--random` makes later goals random strings
of the pieces left.

## What happens

1. The goal is written on the wall behind the tables (the wall is raised to 2 m in this mode), stroke by stroke.
2. The robots spell it on their tables: the normal task, `agents.py` unchanged (including helping the other robot).
3. Goal reached: confetti, the spelled pieces vanish, the wall is painted over, the next goal is written.
   Goal not reached (the `--time` limit): the goal is struck through in red, the spelled pieces are taken off the
   tables without confetti, then the next goal (or the end with `--on-timeout stop`).

No pieces are added between goals. A goal is only chosen if the pieces left in the room hold its symbols; a
`--sentences` goal that cannot be spelled any more is skipped (with a message). Between goals, `new_goal()` gives
the Blackboard the new words and keeps what the robots know about the pieces still on the floor.

## Videos

With `--video vid`, `multiple_run.py` writes:

- `vid/multiple_run.mp4`: the overview camera at 4x real time (one frame every 0.2 simulated seconds), and
  `vid/multiple_run.timeline.json`: the simulated time and caption of every frame, and the slow windows.
- `vid/multiple_run_condensed.mp4`, made from the two at the end: 60x real time, 2x in the slow windows (the 6 s
  before every placement, the goal being written, reached or struck through), with a caption saying what happens
  and how fast it plays.

How it works: a raw frame stands for 0.2 simulated seconds; at speed v it lasts 0.2 / v seconds in the condensed
video. At 30 fps a slow frame is shown several times and most fast frames are skipped. Other speeds, without
running again:

```bash
python3 spell_search/video.py vid/multiple_run.mp4 --fast 30 --slow 4
```

A video from `run.py` can be condensed too. `run.py` writes no timeline, so the placements are taken from its
`--json` file:

```bash
python3 spell_search/run.py --headless --video vid --json vid/run.json
python3 spell_search/video.py vid/run.mp4 --events vid/run.json
```

To slow down another moment in `multiple_run.py`, call `rec.slow(t0, t1, "caption")` with simulated times (for
example from `bb.events`) before `rec.close()`.
