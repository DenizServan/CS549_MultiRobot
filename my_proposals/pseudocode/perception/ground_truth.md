# perception/ground_truth.py

True symbols and poses. Only for evaluation and training labels; the reader never uses it.

## getTruth(C, piece_names)

1. for each piece frame:
   1. R = rotation matrix, symbol = text after "char_", k = index in SYMBOLS
   2. tilt = acos(|R[2,2]|)
   3. top_origin = frame position + R z-axis x PIECE_THICKNESS   (point on the top face above the origin)
   4. yaw = atan2(R[1,0], R[0,0])
   5. append {name, symbol, k, xy = top_origin.xy, z = frame z, yaw, tilt, flat = tilt < FLAT_TILT_DEG [5]}
2. return the list
> xy is the top-face point because that is what the reader measures for a tilted piece (same as origin when flat).
> For a tilted piece this yaw (projected x axis) differs from the reader's laid-flat yaw by up to ~4 deg at 30 deg tilt.

## matchRead(read, truth)
1. d = distance from read.xy to every true xy
2. return the nearest piece if d < MATCH_DISTANCE [5 cm], else None

## isRight(read, piece, templates)
1. False if piece is None or read.k != piece.k
2. d = |wrapAngle(read.yaw - piece.yaw)|
3. True if d < ANGLE_TOLERANCE_DEG [10], or sym180 and |d - 180| < 10

## labelDescription(desc, truth, templates, label_covered = False)
1. if cut, or occluded and not label_covered: return (-1, nan)
2. for each true piece within TEMPLATE_HALF_Y + MATCH_DISTANCE (0.24 m) of the blob centre:
   share = fraction of desc.top explained by that piece at its true pose (explainedMask, tol 8 mm)
3. best = piece with the highest share
4. reject if share < LABEL_EXPLAINED_SHARE [0.9] or best tilt > LABEL_MAX_TILT_DEG [30]
5. reject if getVisibleShare < LABEL_MIN_VISIBLE [0.6]   (every blob: a fragment cannot tell the symbol)
   - getVisibleShare: share of the piece's stroke points (every 4th) with an outline point within 8 mm
6. return (best.k, best.yaw)
