# motion/spread.py

Taking the top piece off a pile, putting it down alone, reading it there. Actions are generators.

## isInPile(C, entry, robot, dropped)
1. (stacked OR tilt > MAX_TILT_DEG) AND not occluded AND not alone AND isUsable
2. AND fewer than MAX_TRIES_PER_PIECE [2] earlier drops within 0.15 m of it (world["dropped"])
   > a dropped piece is re-read as a NEW map entry (tries 0), so without this a robot could try the same spot forever

## getSpreadEntry(world, xy, robot): nearest isInPile entry

## getSetAsideSpot(world, robot, z, closing)
1. for reach in SET_ASIDE_REACHES (0.75 m, then 0.65 m): 16 points that far around the base
2. keep: inside the room, clear of tables/bases, >= SET_ASIDE_MIN_GAP [0.3 m] from every map entry, isFarFromOthers
3. farthest from the map entries first ; first one with IK above it AND down at height z (what putDown needs)
   > checking only above it chose spots 0.75 m away where the arm could not reach down to the floor: the robot then
   > lifted the piece and dropped it straight back onto the pile

## spreadPiece(world, robot, entry)           generator -> (symbol or None, reason)
1. tries += 1 ; driveNextTo(entry xy) ; one wrist look from 0.45 m
2. grasp = getGeometricGrasp(wrist camera) ; none -> "no free straight stroke to grasp"
3. IK pre-grasp + grasp ; move down
4. TRUTH: name = getHeldPiece ; none -> "the fingers miss the piece"
5. attach ; lift
6. spot = getSetAsideSpot ; down = spot and putDown(floor, spot, turn 0)
7. Blocked before grasping -> goHome, "the other robot was in the way"
8. not down -> attach the piece to the floor where it is (it falls back) ; world["dropped"] += grasp xy ;
   removeNear(entry xy) ; goHome ; settle ; return "could not put it down alone (dropped it)"   (nothing marked alone)
9. removeNear(entry xy) ; goHome ; settleFreePieces
10. best = lookClosely(spot, match_distance = SPREAD_PIECE_RADIUS [0.15])   (spot = where the GRASP point went down)
11. mark alone only entries within 0.15 m of spot ; goHome
12. return best.symbol if best.conf >= CONF_ACCEPT else None
