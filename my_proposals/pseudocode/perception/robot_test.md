# perception/robot_test.py

One robot, task scene (scattered pieces, near walls, piles): read, drive, re-read with the wrist, grasp, turn upright. For watching
perception in the scene. Truth only scores reads and decides whether a grasp holds.

## main (command line: --reader, --seed, --targets [6], --headless)

1. prm.CONF_* = READER_THRESHOLDS[reader] ; C = buildScene(WORD, seed) (task scene, has piles) ; robot = "p1"
2. (the scene already has piles)
3. templates ; classifier (CNN from cnn/ or template)
4. rows, visited, uncovered = [], [], []
5. repeat `targets` times:
   1. target, reads = getNextTarget(...) ; stop if None ("no trusted read left in view")
   2. row, now_at = handleTarget(target, ...)
   3. visited += now_at (where the piece is now)
   4. if it was set aside from a pile: uncovered += target.xy (the piece below goes next)
6. printSummary(rows)

## getNextTarget(C, view, robot, templates, classifier, floor_z, visited, uncovered)
1. reads = readPicture(mast camera)
2. ok = reads with conf >= CONF_ACT and more than VISITED_DISTANCE [15 cm] from every visited spot
3. priority: pile pieces first (stacked, or near an uncovered spot), then nearest to the base
4. return (best of ok or None, reads)

## handleTarget(target, ...)
1. driveTo(getGrasp(target).xy): 12 spots PICK_DISTANCE [0.65 m] around the grasp point, first with IK above it;
   jump the base there (straight, no path planning) ; fail -> "no base spot"
2. Wrist re-read
   1. IK: gripper above target.xy at z_top + 0.45 m, closing axis sideways
   2. near = wrist reads within 7 cm of the target ; best = most confident
   3. if best.conf >= CONF_ACCEPT: use the wrist read, else keep the mast read
3. scoreRead vs truth (getTruePiece: within 5 cm, top height closest) ; addMarker (green right / red wrong)
4. no true piece there -> "no piece there"
5. grasp_xy, closing = getGrasp(read) ; z = getTopHeightAt(...) - 0.04 + 0.02
6. IK pre-grasp (z + 0.15) and grasp, closing as is or turned 180 deg ; none -> "no grasp IK"
7. move down ; graspHolds via truth (1.5 cm, 15 deg, 1.5 cm) ; no -> "grasp misses"
8. attach, lift
9. Put down upright
   1. stacked read: try getSetAsideSpot (16 points 0.35 m around the pile, farthest from seen pieces, with IK)
   2. putDown(place, turn = -read.yaw) (half-turn + re-grasp if the wrist cannot turn far enough)
   3. if it fails beside the pile: try in place ; still fails -> "held, could not put down"
10. attach to floor, arm home, settlePieces ; final yaw from truth
11. return (row, where the piece is now)
> Upright here is yaw 0; motion/place.py uses UPRIGHT_YAW = -pi/2.

## printSummary(rows)
1. one line per target: pile?, mast symbol, read symbol, truth, source (mast/wrist), conf, xy err, yaw err, grasp err, z err, final yaw, result
2. pile pieces vs other pieces: reads right, grasps that hold
