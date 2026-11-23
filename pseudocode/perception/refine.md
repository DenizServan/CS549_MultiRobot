# perception/refine.py

Exact angle and piece origin of a recognised symbol, plus fit checks.

## fineFit(desc, templates, k, yaw)

1. strokes, marks = fine grids (5 mm) ; s = FINE_SHIFT_CELLS [8] ; cell = 5 mm
2. for each da in FINE_ANGLES (-6 .. +6 deg, 1 deg steps):
   1. a = yaw + da
   2. O, D, H = getObservedGrids(desc, a, cell, s)
   3. scores, overlap = scoreAllShifts for template k only
   4. (dy, dx) = best shift
   5. if best so far: remember (score, a, dx, dy, precision = overlap / |O|)
3. centroid = desc.centre + turnPoints(((dx - s) x cell, (dy - s) x cell), a)
   > the template centroid sits (dx - s, dy - s) cells from the blob centre, in the frame turned by a
4. origin = centroid - turnPoints(templates.centroid[k], a)
   > from the stroke centroid back to the piece frame origin (where the grasp marker is defined)
5. return {yaw = a, xy = origin, score, precision}
> precision < COVERAGE_THRESHOLD [0.85]: the template explains too little of the blob -> another piece is in it.

## explainedMask(xy, templates, k, yaw, origin, tolerance [EXPLAINED_TOLERANCE 1.2 cm])

1. if no points: return empty
2. local = rotatePoints(xy - origin, yaw)               points in the piece frame
3. dist = distance from each local point to the nearest template stroke point (KD-tree)
4. return dist < tolerance
