# perception/blob.py

Turns one blob into the flat description that both readers use.

## describeBlob(blob, floor_z, blobs)

1. Find the top face (getTopFace)
   1. n = plane normal of all points: smallest singular vector of the centred points (getPlaneNormal), flipped to point up
   2. on_face = points within PLANE_INLIER_TOLERANCE [1 cm] of that plane
   3. refit n on the on_face points, recompute on_face with the new plane
   > Removes side-wall points the segmentation kept.
2. face = points[on_face], face_rgb = rgb[on_face], centre3 = mean of face
3. Lay it flat
   1. R = getFlatteningRotation(n): Rodrigues rotation about the axis n x (0,0,1) that turns n onto vertical
   2. flat = (face - centre3) @ R.T + centre3
   > Rotating about a horizontal axis keeps the piece's heading, so the angle read later is its yaw before tilting.
4. dark = face points with max(R, G, B) < DARK_THRESHOLD [25]   (the black glyph-bottom dots)
5. top = flat x-y
6. z_top = highest blob point
7. hidden = points of the blobs in blob.covered_by, rotated with the same R about centre3, x-y only
8. tilt = angle between n and vertical
9. stacked = z_top - floor_z > STACKED_HEIGHT [6.5 cm]
10. underside = share of dark face points > MAX_DARK_SHARE [0.5]   (a piece's black base layer, not a top face)
11. return {top, dark (flat x-y), hidden, centre = mean(top), z_top, tilt, stacked, cut, occluded, underside}
> If dark is empty on every blob, the dots render brighter than 25 and the dot score is skipped.

## subDescription(desc, keep_top, keep_dark)

1. copy desc with only the selected top and dark points
2. centre = mean of the kept top points
> Used by reader.py to split touching pieces. cut / occluded / hidden stay those of the whole blob.
