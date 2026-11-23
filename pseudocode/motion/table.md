# motion/table.py

The table cells and where the base stands to reach one.

## getCells(C, table)
1. the 9 frames "area_<k>_<L|R>" (k = 1..9) ; their xy
2. sort far row first (largest x), then from the reader's left (largest y)
3. if SKIP_CENTRE_CELL: drop the cell within 5 cm of the table centre
4. return 8 cell centres in reading order

## getTableTop(C, table)
1. table z + half its height

## getStandSpots(C, robot, table, xy)
1. for each of the 4 table sides (x-, x+, y-, y+):
   1. p = xy moved straight out to the table edge + TABLE_STANDOFF [0.55 m]
   2. if isFree(p): spot = (p, yaw facing xy)
2. sort the spots nearest to the robot first
