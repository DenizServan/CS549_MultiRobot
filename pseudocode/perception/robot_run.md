# perception/robot_run.py

The team's full two-robot task with this perception package plugged in.

## main (command line: --reader, --team PATH, everything else passed to the team's run.py)

1. check that PATH/agents.py exists
2. put the team folder on sys.path ; import agents, coordination, run
3. rows = []
4. agents.read = makeRobotReader(loadTemplates(), classifier, rows)     replaces the team's reader
5. setThresholds([agents, coordination], reader)
   1. (act, verify, accept) = READER_THRESHOLDS[reader]   cnn (0.02, 0.01, 0.02), template (0.15, 0.075, 0.15)
   2. write them into both team modules
6. run the team's main with the remaining arguments
7. finally: printReadSummary(rows) ; optionally dump rows to JSON (ROBOT_RUN_ROWS)

## makeRobotReader -> readForRobots(world, tpl, camera, exclude)
1. reads = readPicture(world.view_cam, world.C, camera, templates, world.floor_top, classifier)
2. for each read: matchRead vs truth, append a row (mast/wrist, conf, right, symbols, yaw error, xy, z_top, tilt)
   (summary only; the robots never see it)
3. return reads renamed to the team's fields: symbol, yaw, xy, conf, z_top, stacked, prec, alts

## printReadSummary(rows)
1. for mast (limit = act) and wrist (limit = accept): reads, trusted, trusted wrong, measured threshold (getThreshold)
> The team's code places pieces with the TRUE in-hand pose, so read errors show as wrong pieces / failed grasps only.
