# perception/reader.py

Runs the whole perception pipeline for one picture.

## readPicture(view, C, camera_name, templates, floor_z, classifier = classifyTemplate)

1. rgb, points, valid, size = takePicture(view, C, camera_name)          camera.py
2. blobs = getBlobs(rgb, points, valid, size, getIgnoreBoxes(C), floor_z)  segmentation.py
3. reads = []
4. for each blob:
   1. desc = describeBlob(blob, floor_z, blobs)                             blob.py
   2. skip it if desc.underside (black base layer)
   3. reads += readDescription(desc, templates, classifier)
5. return reads

## readDescription(desc, templates, classifier, depth = 0)

1. c = classifier(desc, templates)            -> k, coarse yaw, margin, alts, fit_check
2. fit = fineFit(desc, templates, c.k, c.yaw)  -> exact yaw, origin xy, score, precision
3. conf = c.margin x coveragePenalty(fit.precision)
4. if c.fit_check (BOTH readers set it): conf x= fitPenalty(fit.score, getPointsPerCell(desc.top))
   - getPointsPerCell: number of top points / number of occupied 1 cm cells
5. if isUntrusted(desc): conf = 0
   - cut (and DISTRUST_CUT) OR occluded (and DISTRUST_OCCLUDED) OR tilt > MAX_TILT_DEG [15]
6. read = {symbol, k, yaw = fit.yaw, xy = fit.xy, conf, alts, precision, score, z_top, tilt, stacked, cut, occluded}
7. if fit.precision >= 0.85 OR depth >= MAX_SPLIT_DEPTH [2]: return [read]
8. Split touching pieces
   1. on_top = explainedMask(desc.top, k, fit.yaw, fit.xy) ; on_dark = same for dark points
   2. if >= MIN_SPLIT_POINTS [40] points on: reads += readDescription(only those points, depth = 2)   (no further split)
   3. if >= 40 points off: reads += readDescription(the other points, depth + 1)                    (may split again)
   4. return reads, or [read] if both parts were too small

## main

1. buildScene, loadTemplates, test camera at (-2.5, 2.5)
2. readPicture and print each read: symbol, xy, yaw, conf, cut
