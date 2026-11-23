# motion/place.py

Putting the held piece upright in a table cell, using the READ pose. Actions are generators.

## getPlaceTarget(read, templates, cell_xy)
1. origin = cell - rot(UPRIGHT_YAW) @ centroid[k] ; target = origin + rot(UPRIGHT_YAW) @ grasp_marker[k]
2. turn = UPRIGHT_YAW - read.yaw

## putDown(C, robot, piece, surface, place_xy, z, hold, turn)     generator -> True if down
1. goDown(angle, now): IK above / at place_xy with the last joint pre-turned either way
2. up to 3 times: whole turn possible -> moveArm up, down, attach(surface), up -> True
   else half turn: down, let go, re-grasp from the other side (hold + 180), continue with the other half
3. return False

## settleFreePieces(world)
1. every piece whose parent is not a gripper ; settlePieces(those, without bases, drop = 0)
> drop 0: pieces that lie still stay where they are; a piece held by the other robot is not touched.

## placePiece(world, robot, held, table, cell_xy)                  generator -> "" or reason
1. target, turn = getPlaceTarget ; z = table top + 0.02 + PLACE_CLEARANCE
2. up to PLACE_TRIES [10] times:
   1. for spot in getStandSpots(table, cell) (free sides only):
      1. skip if no IK above target from there ; claim(robot, cell, spot)
      2. driveTo(spot) or try the next ("no path to the table")
      3. putDown(...) -> placed ; putDown fails -> "no arm solution for putting it down", stop trying
   2. Blocked -> "the other robot was in the way"
   3. placed or no arm solution: stop
   4. otherwise (no free side / no path, usually the other robot is there): clear the claims, goHome, KEEP HOLDING the
      piece, wait PLACE_WAIT_STEPS [50] steps, try again
3. still not placed: attach(floor, piece) (dropped where it is)
4. goHome ; settleFreePieces ; return reason
