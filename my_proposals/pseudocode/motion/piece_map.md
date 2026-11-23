# motion/piece_map.py

The robots' SHARED memory of the pieces. entry = {read, tries, ruled_out (set), alone, claimed (robot or None)}.

## updateMap(entries, reads, C, camera)
1. for each read:
   1. nearest entry within MAP_MERGE_DISTANCE [5 cm]?
      - yes: replace its read if this read's conf >= the entry's conf (tries, ruled_out, alone kept) ; mark it seen
      - no: append a new entry {read, tries 0, ruled_out {}, alone False, claimed None}
2. if C and camera are given (forgetting):
   1. (centre, radius) = getViewRadius(C, camera): disc FORGET_FRACTION [0.8] of the shorter half side of the view
   2. drop every entry that lies in that disc, outside the ignore boxes, was not matched by a read now, and is not
      claimed   (its piece was taken away or moved)

## isUsable(C, entry, robot)
1. tries < MAX_TRIES_PER_PIECE [2] AND not claimed by the other robot AND isFarFromOthers(entry xy)

## findPiece(C, entries, symbol, xy, robot)
1. usable = entries read as symbol, symbol not ruled out, isUsable
2. sure = usable with conf >= CONF_ACT
3. maybe = usable that are isReadable (not cut, not covered, tilt <= MAX_TILT_DEG [15])
4. nearest of sure, else nearest of maybe, else None

## isReadable(read): not cut AND not occluded AND tilt <= MAX_TILT_DEG

## findUnreadable(C, entries, xy, robot)
1. nearest entry with conf < CONF_ACT, tries 0, usable, not stacked, isReadable   (worth one wrist look)

## removeNear(entries, xy): drop entries within 5 cm
## getViewpoints(C): grid every EXPLORE_SPACING [1.5 m] over the room
