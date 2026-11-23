# perception/confidence.py

Turns scores and fit checks into one confidence number. Not a probability; template and CNN scales differ.

## wrapAngle(a)
1. return (a + pi) mod 2 pi - pi

## templateMargin(scores, k, angle_index, sym180)
1. best = scores[angle_index, k]
2. d = angle difference of every row to the best angle
3. same_look = d < DIFFERENT_ANGLE_DEG [25] ; if sym180: also |d - 180 deg| < 25
4. different = every entry except (same_look rows, column k)
5. competitor = max over different entries
6. return clip((best - competitor) / best, 0, 1)

## coveragePenalty(precision)
1. precision >= COVERAGE_THRESHOLD [0.85]: return 1
2. else: return max(0, (precision - 0.60) / (0.85 - 0.60))

## fitPenalty(fit_score, points_per_cell)          (both readers)
1. (lo, hi) = FIT_DENSE (0.55, 0.70) if points_per_cell >= DENSE_POINTS_PER_CELL [4], else FIT_SPARSE (0.30, 0.40)
2. return clip((fit_score - lo) / (hi - lo), 0, 1)
> Catches confident reads of fragments / cut-off pieces whose template does not fit.

## calibrate(margin, calibration)                  (CNN reads only)
1. return np.interp(margin, calibration.margin, calibration.conf)
> Current cnn_weights.pt (task scene): 0 -> 0, 0.310 -> 0.02, 0.620 -> 0.03, 0.630 -> 0.10, 1 -> 1.
> The robots use READER_THRESHOLDS["cnn"] = (0.02, 0.01, 0.02) on this scale.
