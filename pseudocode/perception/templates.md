# perception/templates.py

Reads the 36 letter models from characters.g (geometry only, no ground truth).

## loadTemplates(cells = (COARSE_GRID_CELL [1 cm], FINE_GRID_CELL [5 mm]))

1. M = new Config with characters.g
2. for each symbol in SYMBOLS:
   1. frame = "char_<symbol>"
   2. points = getStrokePoints(frame)
      1. for each child named "<char>_s<k>" that is a box:
         1. L, W = box length and width ; centre = relative position ; a = its rotation about z
         2. grid of points every TEMPLATE_SAMPLE_STEP [2 mm] covering L x W
         3. turn by a, move to centre
      2. stack all strokes -> P x 2 points in the PIECE frame
   3. marks = relative x-y of children "<char>_hole<k>" (getMarks)  -> black dot centres
   4. centroid = mean of points
   5. grasp = (relative x-y, angle about z) of child "<char>_grasp" (getGrasp)
   6. sym180 = getSym180(points)
      1. p = points - mean ; rasterize p and -p on a 5 mm grid
      2. True if IoU of the two grids > SYM180_THRESHOLD [0.85]
3. for each cell size:
   1. stroke grid of each symbol = rasterize(points - centroid, cell)  window 2 x 0.12 by 2 x 0.19 m
   2. mark grid of each symbol = getMarkGrid: a small cross (radius DOT_RADIUS [6.7 mm]) at every mark, minus centroid
   3. grids[cell] = (36 stroke grids, 36 mark grids)
4. return {symbols, points, marks, centroid, grasp, sym180, grids}
> Grids are centred on the stroke CENTROID, not on the piece origin. refine.py converts back to the origin.

## Helpers

- getGridShape(cell, margin): rows = 0.38 m / cell + 2 margin, cols = 0.24 m / cell + 2 margin
- rasterize(xy, cell, margin): boolean grid around (0, 0), rows = y, cols = x; True where a point falls; points outside dropped
- rotatePoints(xy, a): coordinates in a frame turned by a  (= rotate the points by -a)
- turnPoints(xy, a): rotate the points by +a

## main

1. loadTemplates; print the symbols that look the same after a half turn
2. show the 36 fine stroke grids with marks
