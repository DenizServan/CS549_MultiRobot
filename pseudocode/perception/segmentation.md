# perception/segmentation.py

Cuts one picture's point cloud into blobs, one per visible surface.

## getBlobs(rgb, points, valid, image_size, ignore_boxes, floor_z)

1. Height band and ignore boxes (getPieceMask)
   1. h = points.z - floor_z
   2. in_band = valid AND SEG_MIN_HEIGHT [1.2 cm] < h < SEG_MAX_HEIGHT [25 cm]
   3. in_box = point inside any ignore box (tables, bases)
   4. keep = in_band AND NOT in_box ; hidden = in_band AND in_box
2. Drop steep pixels (getUpFacing)
   1. reshape points to H x W x 3
   2. along rows and along columns: step to the previous and to the next pixel; keep the step with the smaller height
      change (so a pixel on the edge of a flat top takes its step on the top)
   3. normal = cross(row step, column step)
   4. up-facing if the normal is within SEG_MAX_SLOPE_DEG [60] of vertical
   5. keep = keep AND up-facing
   > This removes the side walls of pieces, which would otherwise join a top face to the piece below.
3. if nothing is kept: return []
4. Group pixels into surfaces (getSurfaceLabels)
   1. all pairs of horizontally / vertically neighbouring pixels (getNeighbourPairs)
   2. a pair is joined if both pixels are kept AND |z_a - z_b| < SEG_DEPTH_JUMP [1.5 cm]
   3. connected components of that graph -> one label per pixel (-1 for pixels not kept)
   > A piece lying on another is ~4 cm higher at its edge -> separate label.
   > Two pieces touching at the same height -> ONE label (reader.py splits them later).
5. Who lies on whom (getCoverings)
   1. neighbouring pixel pairs with two different labels
   2. if one side is higher by more than 1.5 cm: the higher label lies on the lower label
   3. covers = {lower label: set of labels lying on it}
6. Cut pixels
   1. border = pixels within BORDER_MARGIN_PX [2] of the image edge (getBorderPixels)
   2. OR within 2 px of a hidden pixel (getNearHidden: dilate the hidden mask)
7. Build the blobs
   1. sort pixel indices by label, walk the groups
   2. skip label -1, groups with < SEG_MIN_POINTS [25] pixels, groups wider than SEG_MAX_EXTENT [0.6 m]
   3. blob = {points, rgb, pixels, cut = any pixel in border}
8. Covering as blob indices
   1. covered_by = indices of the kept blobs whose labels lie on this one
   2. occluded = covered_by is not empty
9. return blobs

## main

1. buildScene, test camera at (-2.5, 2.5), takePicture, getBlobs
2. print how many blobs, how many cut, how many covered
3. scatter plot of the blobs (x marker = cut or covered)
