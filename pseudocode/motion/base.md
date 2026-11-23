# motion/base.py

Driving the base: straight if free, else A* around tables and the other robot. Pieces are not obstacles.

## getBasePose(C, robot)
1. base joints (x, y) + xy of base_origin_<i> ; yaw = third base joint

## getObstacles(C, robot)
1. each table: (centre, half size + BASE_HALF [0.45])
2. for the other robot, boxes of half size BASE_HALF + OTHER_BASE_HALF (0.85 m) at:
   1. its base now
   2. its claimed work point (where its arm reaches) and its claimed base goal
   3. if the other robot has priority (earlier in ROBOTS, i.e. p1 for p2): every CORRIDOR_STEP [0.25 m] on the line
      from its base to its goal   (p2 keeps out of p1's way)

## isFree(C, robot, xy)
1. inside the room shrunk by 0.45 AND outside every obstacle box

## getPath(C, robot, start, goal)
1. straight line free (checked every 5 cm)? -> [goal]
2. else A* on a 10 cm grid (8 neighbours), start/goal cells forced free; shortcut the waypoints ; None if unreachable

## moveBase(C, robot, xy, yaw, max_wait)    generator
1. moveJoints(base joints, (xy - origin, yaw), steps of MAX_BASE_STEP [5 cm] / MAX_TURN_STEP [0.1 rad])

## driveTo(C, robot, xy, yaw)              generator -> True if it got there
1. goHome (arm folded while driving)
2. max_wait = MAX_WAIT_STEPS [150] for p1, YIELD_WAIT_STEPS [20] for p2 (p2 gives way sooner)
3. repeat up to REPLAN_TRIES + 1 [7] times:
   1. path = getPath(here, xy)   (straight line if the base now stands in a non-free spot)
   2. no path (e.g. the other robot stands in the way): wait max_wait steps, try again
   3. for each waypoint: moveBase toward it (heading along the way, the last one: yaw, turned the short way)
      - Blocked (the other robot stayed in the way): plan again from here
   4. all waypoints reached: return True
4. return False

## copyWithBase(C, robot, xy, yaw)
1. copy of C with the base at (xy, yaw) and the arm at home   (reach checks before driving)
