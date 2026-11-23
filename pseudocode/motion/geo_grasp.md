# motion/geo_grasp.py

A grasp from geometry only (no symbol): a straight piece of stroke with room for both fingers.

## getGeometricGrasp(view, C, camera, xy, floor_z)
1. Picture and blob
   1. rgb, points, valid, size = takePicture(camera)
   2. blobs = getBlobs(...) that are NOT occluded ; none -> None
   3. blob = the one with a point nearest xy ; if that point is > 10 cm away -> None
   4. P = blob points ; obstacles = all valid points of the picture
2. Candidates
   1. cells = the blob's points rounded to a GEO_CANDIDATE_STEP [1 cm] grid
   2. for each cell centre c:
      1. idx = blob points within GEO_NEIGHBOUR_RADIUS [3 cm] of c ; skip if < GEO_MIN_NEIGHBOURS [30]
      2. getStroke(points[idx]): PCA of their x-y
         - along = main direction, across = perpendicular
         - width = spread across ; centre = middle across ; elongation = sqrt(var along / var across)
      3. skip if elongation < GEO_MIN_ELONGATION [2] or width > GEO_MAX_STROKE_WIDTH [4 cm]   (corner, two strokes)
      4. top = median z of the neighbours ; z_grasp = top - 0.04 + 0.02
      5. getFingersFree(obstacles, centre, along, width, z_grasp):
         two finger boxes beside the stroke (FINGER_GAP [5 mm] away, FINGER_DEPTH [2 cm] thick, FINGER_WIDTH [2 cm] long);
         blocked if any obstacle point inside is higher than z_grasp - FINGER_CLEARANCE [1 cm] ; skip if blocked
      6. keep the candidate closest to the blob's mean xy: (centre, closing angle across the stroke, top)
3. return (grasp xy, closing angle, top) or None

## getHeldPiece(C, names, templates, grasp_xy, closing, z)      (TRUTH: fingers are not simulated)
1. for each true piece:
   1. grasp point (at the top-face height implied by z) expressed in the piece frame
   2. skip if farther than 2 mm + GEO_TOL_STROKE [4 mm] from its stroke points
   3. stroke direction at that point: PCA of the template points nearby (getStroke)
   4. skip if the closing axis is not within GEO_TOL_ANGLE_DEG [20] of across that stroke
   5. skip if z does not fit the piece's top height there within GRASP_TOL_Z [1.5 cm]
   6. hit (top height, name)
2. return the name of the highest hit, else None
