# motion/score.py

Ground-truth check of the spelled word.

## getCentre(C, piece, templates)
1. true stroke centroid in the room = frame position + R @ (centroid[k], 0)

## scoreTable(C, names, cells, letters, templates)
1. truth = getTruth ; centre of every piece
2. for each (cell, letter):
   1. near = pieces with centre within CELL_MATCH_DISTANCE [12 cm] of the cell ; none -> {want, got "-", ok False}
   2. p = the nearest
   3. yaw_err = |p.yaw - UPRIGHT_YAW| (min with its 180 deg turn if sym180)
   4. pos_err = |centre - cell|
   5. ok = p.symbol == letter AND yaw_err < YAW_OK_DEG [10] AND pos_err < POSITION_OK [4 cm]
3. return rows
