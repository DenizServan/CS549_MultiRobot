# motion/ : two robots spell a word at the same time with the perception package

The scene is the one task scene (`perception/scene_builder.buildScene`): every symbol once plus the word's letters
twice more; 30 % of the pieces dropped in 3 piles, the rest scattered over the floor, a quarter of those within
0.4 m of a wall. p1 puts the first half of the word on `table_left`, p2 the second half on `table_right`.

Both robots move kinematically and **at the same time**: every motion is a Python generator that takes one small step
per `next()` (at most 5 cm / 0.1 rad for the base, 0.05 rad per arm joint), and `spell.py` steps p1, then p2, then
p1, ... Before every step the moving robot checks the gap to the other robot (`clearance.py`: each robot is a set of
balls on its base, arm joints and held piece); if the step would bring them closer than 5 cm it waits. A driving robot
that waits too long plans again around the other one; p2 gives way sooner than p1 and keeps out of p1's path.
Work is claimed: a robot never starts work within 1.5 m of where the other one works or is going.

Sits next to `perception/` (imports it). Every number is in `motion_parameters.py`, including the confidence
thresholds per reader (`READER_THRESHOLDS`, measured with `perception/evaluate.py` on the task scene).

| file | in | out |
|---|---|---|
| `motion_parameters.py` | | every motion constant, thresholds per reader |
| `clearance.py` | both robots' poses | gap between the robots (balls), claims of where each robot works |
| `arm.py` | target joints / gripper pose | KOMO IK; stepwise joint motions that wait for clearance (generators) |
| `base.py` | goal xy | free-space check, A* around tables and the other robot, stepwise driving that re-plans when blocked |
| `table.py` | table name | cell centres in reading order, base spots to reach a cell |
| `piece_map.py` | mast / wrist reads of both robots | shared memory of the pieces (forgets pieces a new picture no longer shows), nearest usable piece of a symbol, viewpoints |
| `pick.py` | map entry | drive next to it, wrist looks (far, closer, from the side), grasp at the read pose (attach); inspect a piece |
| `spread.py` | pile entry on the map | take the top piece off a pile (geometric grasp), put it on free floor, read it there |
| `geo_grasp.py` | wrist picture | a grasp without the symbol: straight stroke piece with room for both fingers; truth check of the hold |
| `place.py` | held piece, cell | drive to the table, turn upright (re-grasp if the wrist cannot turn far enough), put down, PhysX settle |
| `score.py` | final scene | ground-truth check of each cell (symbol, yaw error, centre offset) |
| `spell.py` | word, reader, seed | runs both robots, prints the log, the smallest gap between the robots and the result |

Each robot, whenever it is free, chooses its next action for its next letter: fetch a piece read as the letter →
explore a viewpoint nobody scanned → spread a pile → inspect an unreadable lone piece → wait for the other robot →
give the letter up.

```bash
python3 motion/spell.py                                   # CNN reader, seed 0, "ROBOTICS", viewer
python3 motion/spell.py --word "HELLO" --seed 1
python3 motion/spell.py --reader template --headless
python3 checks/check_clearance.py                         # two robots whose paths cross / one arm in the way
```

Basic on purpose: kinematic robot motion, the arms are only checked against the other robot (not against tables or
pieces), the bases drive over pieces, grasping is attach(). The ground truth is used only to decide whether the
fingers would hold a grasp (pick.fingersHold, geo_grasp.getHeldPiece) and for the score.
To run one action alone while debugging: `arm.runToEnd(C, pickPiece(world, "p1", entry, "R"))`.
