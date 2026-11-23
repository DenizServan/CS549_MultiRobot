# motion/pick.py

Fetching one piece. Actions are generators; world = {C, view, templates, classifier, floor_z, names, entries}.

## getGrasp(read, templates)
1. grasp_xy = read.xy + rot(read.yaw) @ marker_xy ; closing = read.yaw + marker_angle

## scan(world, robot, camera)
1. reads = readPicture(camera) ; updateMap(entries, reads, C, camera) ; return reads

## driveNextTo(world, robot, xy)                generator -> True if there
1. for 12 directions around xy (the one toward the base first):
   1. b = xy + PICK_DISTANCE [0.65] x direction ; skip if not isFree
   2. skip if no IK above xy (0.3 m high) from a copy with the base at b
   3. claim(robot, xy, b) ; if driveTo(b, facing xy): return True
2. return False

## lookClosely(world, robot, read, match_distance [WRIST_MATCH_DISTANCE 7 cm])   generator
1. for (height, shift) in WRIST_LOOKS [(0.45, 0), (0.32, 0), (0.45, 0.10)]:
   1. IK: wrist above read.xy (+ shift sideways), height above read.z_top ; skip if none ; moveArm there
   2. reads = scan(wrist camera)                     (into the shared map)
   3. best = most confident read within match_distance of read.xy so far
   4. stop when best.conf >= CONF_ACCEPT
2. return best, camera

## inspectPiece(world, robot, entry)            generator -> "" if now readable
1. tries += 1 ; driveNextTo ; lookClosely
2. every entry within SPREAD_PIECE_RADIUS [0.15 m] of it gets tries >= 1 (not inspected again) ; goHome

## pickPiece(world, robot, entry, symbol)       generator -> (held, "") or (None, reason)
1. driveNextTo(grasp point of the entry's read) ; fail -> tries += 1, "no spot to stand"
2. best = lookClosely(read)
3. best missing / conf < CONF_ACCEPT / other symbol -> (sure other symbol: ruled_out += symbol) ; tries += 1 ; goHome ; fail
4. read = best ; grasp_xy, closing = getGrasp(read) ; z = getTopHeightAt(...) - 0.04 + 0.02
5. IK pre-grasp (z + 0.15) and grasp (z), closing or closing + 180 deg ; none -> fail
6. moveArm pre-grasp, grasp
7. TRUTH: piece = getTruePiece ; fingersHold? no -> back up, goHome, fail "the fingers miss the piece"
8. attach(gripper, piece) ; lift to pre-grasp ; return held info
9. Blocked anywhere (the other robot stayed in the way): tries += 1 ; goHome ; fail
