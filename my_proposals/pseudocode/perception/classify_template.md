# perception/classify_template.py

Classical reader: compares the blob outline with all 36 templates at 72 angles and small shifts.

## classifyTemplate(desc, templates)

1. table = getScoreTable(desc, templates)                 72 angles x 36 symbols
   1. strokes, marks = coarse grids (1 cm)
   2. for each angle a in COARSE_ANGLES (0, 5, ..., 355 deg):
      1. O, D, H = getObservedGrids(desc, a, 1 cm, SHIFT_CELLS [3])
         1. O = rasterize(rotatePoints(top - centre, a))      outline grid, 3 cells larger on each side
         2. D = same for dark points                          dot grid
         3. H = same for hidden points, dilated once, minus cells that already hold outline
      2. scores = scoreAllShifts(O, D, strokes, marks, H)   (all 36 templates, all 7 x 7 shifts at once)
         1. overlap = |O and T| for every shift: FFT cross-correlation of O with each flipped template
         2. union = |O| + |T| - overlap
         3. if VISIBILITY_AWARE and H not empty:
            unseen = |H and T| for every shift ; union = max(union - UNSEEN_DISCOUNT [0.5] x unseen, overlap)
            > template strokes under a covering piece count only half as missing
         4. iou = overlap / union
         5. if D is empty: score = iou
            else: hits = |D and mark grid| / |D| ; score = iou + DOT_WEIGHT [0.25] x (2 x hits - 1)
      3. table[a, all symbols] = best score over shifts
2. (ai, k) = position of the maximum in the table ; best = table[ai, k]
3. per_symbol = best score of each symbol over all angles
4. alts = up to 3 other symbols with per_symbol > RUNNER_UP_RATIO [0.85] x best
5. margin = templateMargin(table, k, ai, sym180[k])        (confidence.py)
   1. same look = symbol k within DIFFERENT_ANGLE_DEG [25] of ai (or of ai + 180 if sym180)
   2. competitor = highest entry of the table that is NOT a same look
   3. margin = clip((best - competitor) / best, 0, 1)
6. return {k, yaw = COARSE_ANGLES[ai], margin, alts, fit_check = True}
> fit_check True: reader.py also multiplies by fitPenalty. A fragment of a bigger piece fits a simple glyph (L, J, 1)
> with a big margin but a low fit score; without the check those reads were trusted 10-20 % wrong on the task scene.
> Two bright spots 180 deg apart for one symbol -> upside-down doubt (S vs upside-down S differ only in dots) -> margin ~0.
