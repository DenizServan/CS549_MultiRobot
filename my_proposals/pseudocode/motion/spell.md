# motion/spell.py

Two robots spell a word at the same time: p1 the first half on table_left, p2 the second half on table_right.

## main (command line: --word [ROBOTICS], --reader cnn|template, --seed, --headless)

1. Thresholds: prm.CONF_ACT, CONF_VERIFY, CONF_ACCEPT = prm.READER_THRESHOLDS[reader]
2. Scene: C, names, floor_z = buildScene(word, seed)            (the one task scene)
3. world = {C, view, templates, classifier, floor_z, names, entries = [], viewpoints = getViewpoints(C)}
   > `world` is passed to every action; `entries` is the map SHARED by both robots
4. letters = word without spaces ; half = ceil(n / 2)
5. for robot, part in (p1, first half), (p2, second half):
   1. cells = getCells(that robot's table) ; error if more letters than cells (8)
   2. state[robot] = {table, letters = part, cells, i = 0 (next letter), actions, waits, placed}
   3. scan(world, robot, its mast camera)
6. The step loop (until MAX_STEPS [60000] or both robots are done)
   1. for robot in p1, p2:
      1. if the robot has no action: active[robot] = nextAction(world, robot, state, other robot busy?)
         - None -> this robot is done, skip it
         - else: count the action, mark its map entry claimed by this robot, log it
      2. next(active action generator)                        ONE small step of this robot
      3. when the generator finishes (StopIteration -> (text, placed)):
         1. unclaim the entry ; claim(robot) cleared (the robot works nowhere now)
         2. scan with its mast camera (updates / forgets map entries)
         3. if placed: state.i += 1
         4. log the result ; active[robot] = None
   2. steps += 1 ; min_gap = min(min_gap, getMinGap(C))
   3. if show: C.view, sleep STEP_TIME
7. Print time, steps, smallest gap between the robots; score each table (scoreTable, TRUTH); correct cells

## nextAction(world, robot, state, other_busy)
1. while the robot has letters left and actions < MAX_ACTIONS [120]:
   1. letter = state.letters[state.i] ; here = base xy
   2. FETCH: entry = findPiece(C, entries, letter, here, robot) -> fetchAction
   3. EXPLORE: v = getViewpoint(world, robot) -> exploreAction
      - getViewpoint: nearest viewpoint that isFree and isFarFromOthers; removed from the shared list
   4. SPREAD: entry = getSpreadEntry(world, here, robot) -> spreadAction
   5. INSPECT: entry = findUnreadable(C, entries, here, robot) -> inspectAction
   6. WAIT: if the other robot is busy (not waiting itself) and waits < MAX_WAIT_ACTIONS [40] -> waitAction(50 steps)
   7. otherwise: print "given up" ; state.i += 1 ; try the next letter
2. return None (robot done)

## Actions (generators returning (text, placed))
- fetchAction: held = pickPiece ; fail -> text ; removeNear(entries, held.read.xy) ; placePiece(..., cells[i])
- exploreAction: claim(viewpoint) ; driveTo(viewpoint) (the scan happens in the loop when it ends)
- spreadAction: spreadPiece ; text says what the piece reads alone
- inspectAction: inspectPiece (wrist look at an unreadable lone piece)
- waitAction(n): yield n times
