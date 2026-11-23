"""
Driving the mobile base: a straight line if it is free, otherwise an A* path on a grid around the tables and the
other robot (where it stands now and where it is going).

    getObstacles(C, robot)                  ->  boxes (centre, half size) the base centre must stay out of
    isFree(C, robot, xy)                    ->  True if the base can stand at xy
    getPath(C, robot, start, goal)          ->  list of xy waypoints from start to goal (or None)
    copyWithBase(C, robot, xy, yaw)         ->  copy of C with the base moved there (for reach checks)
    moveBase(C, robot, xy, yaw)             generator: base joints there in a straight line, in small steps
    driveTo(C, robot, xy, yaw)              generator: drives the base there (arm at home) along getPath; if the
                                            other robot blocks the way it re-plans around it; returns True if there
    getBasePose(C, robot)                   ->  (x, y, yaw) of the base
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perception"))
import parameters as prm
import motion_parameters as mp
from scene_builder import getRoomLimits, getHalfExtentsWorld
from arm import getJointIndices, moveJoints, goHome, Blocked
import clearance


def getBaseOrigin(C, robot):
    """
    Returns the xy the base joints are measured from (base joint x, y = base position - origin).
    """
    i = prm.ROBOT_NAMES.index(robot) + 1
    return C.getFrame(mp.BASE_ORIGIN_PATTERN.format(i=i)).getPosition()[:2]


def getBasePose(C, robot):
    """
    Returns (x, y, yaw) of the robot's base in the room.
    """
    base_idx, _ = getJointIndices(C, robot)
    q = C.getJointState()[base_idx]
    return np.r_[q[:2] + getBaseOrigin(C, robot), q[2]]


def getObstacles(C, robot):
    """
    Returns the boxes (centre xy, half size xy) the base CENTRE must stay out of: every table, and every other robot's
    base where it stands now, where it is going (its claimed base goal) and where its arm works (its claimed work
    point), grown by BASE_HALF (the base's own half size). A robot also keeps out of the way of a robot listed BEFORE it in ROBOTS (priority): boxes every
    CORRIDOR_STEP along the straight line from that robot's base to its goal. Pieces are not obstacles: the base drives
    over them.
    """
    boxes = []
    for name in prm.TABLE_FRAME_NAMES:
        f = C.getFrame(name)
        boxes.append((f.getPosition()[:2], getHalfExtentsWorld(f)[:2] + mp.BASE_HALF))
    half = np.full(2, mp.BASE_HALF + mp.OTHER_BASE_HALF)
    for other in mp.ROBOTS:
        if other == robot:
            continue
        now, goal = C.getFrame(prm.ROBOT_BASE[other]).getPosition()[:2], clearance.CLAIMS.get(other, {}).get("base")
        work = clearance.CLAIMS.get(other, {}).get("work")
        boxes.append((now, half))
        if work is not None:
            boxes.append((work, half))
        if goal is None:
            continue
        boxes.append((goal, half))
        if mp.ROBOTS.index(other) < mp.ROBOTS.index(robot):          # give way to the robot with priority
            n = int(np.linalg.norm(goal - now) / mp.CORRIDOR_STEP)
            boxes += [(now + (goal - now) * t, half) for t in np.linspace(0, 1, n + 2)[1:-1]]
    return boxes


def isFree(C, robot, xy):
    """
    True if the base centre can be at xy: inside the room (minus BASE_HALF) and outside every obstacle box.
    """
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    if not (x_min + mp.BASE_HALF < xy[0] < x_max - mp.BASE_HALF and y_min + mp.BASE_HALF < xy[1] < y_max - mp.BASE_HALF):
        return False
    return all(np.any(np.abs(xy - c) >= h) for c, h in getObstacles(C, robot))


def isSegmentFree(C, robot, a, b):
    """
    True if every point along the segment a-b (every PATH_CHECK_STEP) is free.
    """
    n = max(2, int(np.linalg.norm(b - a) / mp.PATH_CHECK_STEP) + 1)
    return all(isFree(C, robot, a + (b - a) * t) for t in np.linspace(0, 1, n))


def getFreeGrid(C, robot):
    """
    Returns (free, x0, y0): booleans on a grid of PATH_GRID_CELL squares over the room (True where the base centre can
    be) and the room coordinates of cell (0, 0).
    """
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    xs = np.arange(x_min, x_max, mp.PATH_GRID_CELL)
    ys = np.arange(y_min, y_max, mp.PATH_GRID_CELL)
    free = np.array([[isFree(C, robot, np.array([x, y])) for y in ys] for x in xs])
    return free, x_min, y_min


def getPath(C, robot, start, goal):
    """
    Returns waypoints from start to goal (start excluded), or None if the goal cannot be reached:
    the straight line if it is free; otherwise A* on the free grid (8 neighbours, step length as cost), shortened by
    dropping every waypoint that the line between its neighbours makes unnecessary.
    """
    import heapq
    start, goal = np.asarray(start, float), np.asarray(goal, float)
    if isSegmentFree(C, robot, start, goal):
        return [goal]
    free, x0, y0 = getFreeGrid(C, robot)
    cell = lambda p: (int(round((p[0] - x0) / mp.PATH_GRID_CELL)), int(round((p[1] - y0) / mp.PATH_GRID_CELL)))
    point = lambda c: np.array([x0 + c[0] * mp.PATH_GRID_CELL, y0 + c[1] * mp.PATH_GRID_CELL])
    a, b = cell(start), cell(goal)
    inside = lambda c: 0 <= c[0] < free.shape[0] and 0 <= c[1] < free.shape[1]
    if not (inside(a) and inside(b)):
        return None
    free[a], free[b] = True, True                           # the start and goal cells themselves
    came, cost, todo = {a: None}, {a: 0.}, [(0., a)]
    while todo:
        _, c = heapq.heappop(todo)
        if c == b:
            break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (c[0] + dx, c[1] + dy)
                if (dx or dy) and inside(n) and free[n]:
                    g = cost[c] + np.hypot(dx, dy)
                    if g < cost.get(n, np.inf):
                        cost[n], came[n] = g, c
                        heapq.heappush(todo, (g + np.hypot(n[0] - b[0], n[1] - b[1]), n))
    if b not in came:
        return None
    cells = [b]
    while came[cells[-1]] is not None:
        cells.append(came[cells[-1]])
    points = [start] + [point(c) for c in cells[::-1][1:-1]] + [goal]
    path, i = [], 0                                         # shortcut: from each point jump as far as the line is free
    while i < len(points) - 1:
        j = len(points) - 1
        while j > i + 1 and not isSegmentFree(C, robot, points[i], points[j]):
            j -= 1
        path.append(points[j])
        i = j
    return path


def moveBase(C, robot, xy, yaw, max_wait=mp.MAX_WAIT_STEPS):
    """
    Generator: base joints to (xy, yaw) in a straight line (steps of at most MAX_BASE_STEP / MAX_TURN_STEP).
    """
    base_idx, _ = getJointIndices(C, robot)
    origin = getBaseOrigin(C, robot)
    yield from moveJoints(C, base_idx, [xy[0] - origin[0], xy[1] - origin[1], yaw],
                          np.array([mp.MAX_BASE_STEP, mp.MAX_BASE_STEP, mp.MAX_TURN_STEP]), max_wait)


def driveTo(C, robot, xy, yaw):
    """
    Generator: drives the base (arm at home) along getPath to xy and turns it to yaw. If the other robot blocks a
    step for too long (MAX_WAIT_STEPS for the first robot in ROBOTS, YIELD_WAIT_STEPS for the others, so the second
    one gives way first), or there is no path right now, it waits and plans again from where it is (the other robot
    is an obstacle in getPath), up to REPLAN_TRIES times. Returns True if it got there.
    The straight line is used anyway when the base starts in a spot that is not free (it can then only get out).
    """
    yield from goHome(C, robot)
    max_wait = mp.MAX_WAIT_STEPS if robot == mp.ROBOTS[0] else mp.YIELD_WAIT_STEPS
    for _ in range(mp.REPLAN_TRIES + 1):
        here = getBasePose(C, robot)
        path = getPath(C, robot, here[:2], xy) if isFree(C, robot, here[:2]) else [np.asarray(xy, float)]
        if path is None:                                    # e.g. the other robot stands in the way: wait, plan again
            for _ in range(max_wait):
                yield
            continue
        try:
            for i, w in enumerate(path):
                p = getBasePose(C, robot)
                heading = yaw if i == len(path) - 1 else np.arctan2(w[1] - p[1], w[0] - p[0])
                heading = p[2] + np.arctan2(np.sin(heading - p[2]), np.cos(heading - p[2]))   # turn the short way
                yield from moveBase(C, robot, w, heading, max_wait)
            return True
        except Blocked:
            continue                                        # the other robot is in the way: plan again from here
    return False


def copyWithBase(C, robot, xy, yaw):
    """
    Returns a copy of C with the robot's base at (xy, yaw) and its arm at home: for checking what the arm can reach
    from a spot before driving there.
    """
    import robotic as ry #type: ignore
    Cp = ry.Config()
    Cp.addConfigurationCopy(C)
    base_idx, arm_idx = getJointIndices(Cp, robot)
    origin = getBaseOrigin(Cp, robot)
    q = Cp.getJointState()
    q[base_idx] = [xy[0] - origin[0], xy[1] - origin[1], yaw]
    q[arm_idx] = mp.ARM_HOME
    Cp.setJointState(q)
    return Cp
