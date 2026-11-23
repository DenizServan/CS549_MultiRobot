# perception/cnn/model.py

The CNN's input image and network.

## getInputImage(top, dark, hidden)          points relative to the blob centre

1. img = zeros(3, 64, 64)                      CNN_RESOLUTION [5 mm] per pixel -> 32 cm window
2. for layer, pts in (0 outline, 1 dark dots, 2 hidden region):
   1. pixel (i, j) = floor(pts / 5 mm + 32)
   2. drop pixels outside the image
   3. img[layer, row = j (y), col = i (x)] = 1
3. return img
> Room axes: turning the points turns the image, which is what the angle head relies on.

## Net

1. features: 4 blocks of [conv 3x3, batch norm, ReLU, conv 3x3, batch norm, ReLU, max-pool 2]
   channels 3 -> 32 -> 64 -> 128 -> 128, size 64 -> 32 -> 16 -> 8 -> 4
2. trunk: flatten (128 x 4 x 4) -> dense 256 -> ReLU -> dropout 0.3
3. symbol_head: dense 256 -> 36 scores ; angle_head: dense 256 -> 72 scores (5 deg bins)
4. forward(x) = (symbol scores, angle scores)

## getAngleTarget(yaw, sym180)
1. bin centres = 0, 5, ..., 355 deg
2. bump(a) = Gaussian over bins, sigma CNN_YAW_SIGMA_BINS [1], centred on a, normalised
3. return 0.5 (bump(yaw) + bump(yaw + 180)) if sym180 else bump(yaw)
