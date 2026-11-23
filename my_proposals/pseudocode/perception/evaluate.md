# perception/evaluate.py

Runs the reader on many views of TASK scenes it was not trained on and compares with the truth.

## main (command line: --reader, --seeds, --far [12], --close [40], --trust-covered, --no-visibility)
1. prm.CONF_* = READER_THRESHOLDS[reader]           ("trusted" = what the robots would trust)
2. templates ; classifier
3. for each seed: rows += evaluateScene(seed, ...)
4. printSummary(rows)

## getRandomWord(seed): EVAL_WORD_LENGTH [8] different random symbols (also used by cnn/dataset.py)

## evaluateScene(seed, n_far, n_close, classifier, templates)
1. buildScene(getRandomWord(seed), seed), only the test camera ; addWristTestCamera ; truth
2. for each view in getViews: placeCamera ; for each read in readPicture:
   piece = matchRead ; kind = getPieceKind ; row {seed, far|close, kind, right = isRight, conf}

## getPieceKind(read, piece, C, floor_z)
1. none (no true piece within 5 cm) / cut / covered / tilted (true tilt > 5 deg) /
   stacked (flat but lying on another piece) / wall (flat on the floor within WALL_NEAR [0.385 m] of a wall) / whole

## getViews(C, truth, floor_z, seed, n_far, n_close)
1. far: mast-like camera, uniform xy in the room, 1.7 m above the floor, random heading
2. close: wrist-like camera over a random TRUE piece, + N(0, CLOSE_VIEW_OFFSET_STD [5 cm]),
   CLOSE_VIEW_HEIGHTS (0.32-0.45 m) above its top, random heading      (like the robot's wrist looks)

## printSummary(rows)
1. per camera (far: CONF_ACT, close: CONF_ACCEPT) and kind: reads, % right, % trusted, % of trusted that are wrong
2. measured thresholds: getThreshold(far, 3 %), getThreshold(close, 1 %)   -> copy them into READER_THRESHOLDS
   (run on CALIBRATION_SEEDS 80-89; report final numbers on TEST_SEEDS 100-109)

## getThreshold(rows, max_error)
1. confidences from high to low: the lowest c where reads with conf >= c are wrong at most max_error
