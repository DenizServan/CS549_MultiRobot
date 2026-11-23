# perception/scene_builder.py

Builds THE task scene: every symbol once + the word's letters TASK_SPARES more times; PILE_SHARE of the pieces in
piles, the rest scattered (WALL_SHARE of those close to a wall); PhysX settles everything; cameras are added.

## buildScene(word [ROBOTICS], seed, cameras, verbose)

1. Load the room: C = Config with search_area.g (floor, walls, tables, 2 robots)
2. Which pieces
   1. counts = getTaskCounts(word): every symbol 1, each letter of the word + TASK_SPARES [2] per occurrence
      (ROBOTICS: R B T I C S x3, O x5 -> 52 pieces)
   2. names = getPieceNames(counts): "c<copy>_char_<symbol>"
   3. loadCharacters(C, names): characters.g once per copy layer, pieces not in names deleted
3. floor_z = top of the floor ; rng = default_rng(seed)
4. order = names shuffled ; n_pile = round(PILE_SHARE [0.3] x number of pieces)
5. Piles: centres = placePilePieces(C, first n_pile names, rng, floor_z)
   1. getPileCentres: PILE_ZONES [3] points, each whole disc (PILE_ZONE_RADIUS [0.15] + LETTER_RADIUS) in the room and
      away from tables/bases, >= PILE_ZONE_GAP [1.5 m] apart
   2. each piece -> the pile with fewest pieces: random spot in its 0.15 m disc,
      z = floor + layer x (0.04 + PILE_LAYER_GAP), random yaw, tilt up to PILE_MAX_TILT_DEG [20]   (a tower)
6. Scattered: placePieces(C, the other names, rng, floor_z, centres)
   1. the first WALL_SHARE [0.25] of them: getWallSpot = random wall, distance LETTER_RADIUS .. WALL_NEAR (0.135-0.385 m)
      the rest: uniform in the room shrunk by LETTER_RADIUS
   2. must be outside tables/bases (getOutsideKeepOut) and > PILE_KEEP_OUT [0.6 m] from every pile centre
   3. random yaw ; height map of 1 cm cells: a piece overlapping one already placed lies on it
7. settlePieces(C, names, duration = PILE_SETTLE_DURATION [4 s])   (towers fall into piles)
8. addCameras: mast (child of base, 1.6 m up), wrist (child of gripper), test (free)
9. print the composition ; return C, names, floor_z, camera_names

## settlePieces(C, names, obstacles, duration [3 s], drop [SETTLE_DROP_HEIGHT 0.05])

1. S = new config with only the obstacle boxes (default floor, walls, tables, bases; motion/ leaves bases out)
2. loadCharacters(S, names)                           (only these pieces: a held piece is not touched)
3. each piece's pose from C, lifted by `drop`        (motion/ passes drop 0 after a put-down: still pieces stay)
4. PhysX for `duration` (5 ms steps, gravity and contacts only)
5. max_speed over the last 0.5 s ; copy poses back into C ; return max_speed

## Helpers
- getCountsFromNames(names): {symbol: copies} needed for these names
- getRoomLimits, getKeepOutBoxes, getOutsideKeepOut, getOutlinePoints, getYawPose, getHalfExtentsWorld, getFloorTop
- cameras: getCameraAttributes, addCamera, addMastCameras, addWristCameras, getLookDownQuaternion, placeTestCamera
