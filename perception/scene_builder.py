"""
Builds THE task scene once: the room, tables and robots from search_area.g, then the pieces from characters.g:
every symbol once plus the word's letters TASK_SPARES more times. A share PILE_SHARE of the pieces is dropped in
PILE_ZONES piles, the rest is scattered over the free floor (a share WALL_SHARE of them close to the walls; pieces
that overlap are stacked). Then PhysX settles everything and the cameras are mounted: a mast and a wrist camera per
robot, and one free test camera.

    buildScene(word, seed, cameras)  ->  (C, piece_names, floor_top, camera_names)
    settlePieces(C, names, ...)        lets PhysX settle the named pieces again (after a put-down)

Nothing runs when this file is imported. Running it directly builds the scene and opens the viewer.
"""

import numpy as np
import robotic as ry #type: ignore
import parameters as prm


# ------------------------------------------- 1. WHICH PIECES ------------------------------------------------------------

def getTaskCounts(word):
    """
    Returns {symbol: copies} of the task scene: every symbol once, plus TASK_SPARES copies per letter of the word.
    """
    counts = {s: 1 for s in prm.SYMBOLS}
    for ch in word.upper():
        if ch in counts:
            counts[ch] += prm.TASK_SPARES
    return counts


def getPieceFrameName(copy, symbol):
    """
    Returns the frame name of one copy of a symbol, e.g. (1, "K") -> "c1_char_K".
    """
    return f"c{copy}_{prm.CHARACTER_FRAME_PREFIX}{symbol}"


def getPieceNames(counts):
    """
    Returns the frame names of all pieces for {symbol: copies}, copy by copy, symbol by symbol.
    """
    layers = max(counts.values())
    return [getPieceFrameName(copy, s) for copy in range(layers) for s in prm.SYMBOLS if copy < counts.get(s, 0)]


def getCountsFromNames(names):
    """
    Returns {symbol: copies} that contains these piece names ("c2_char_O" needs 3 copies of O).
    """
    counts = {}
    for n in names:
        copy, symbol = n.split("_" + prm.CHARACTER_FRAME_PREFIX)
        counts[symbol] = max(counts.get(symbol, 0), int(copy[1:]) + 1)
    return counts


# ------------------------------------------- 2. LOADING THE CHARACTERS ---------------------------------------------------

def deleteFrameAndChildren(C, name):
    """
    Removes a frame and its children (characters.g is loaded whole, unwanted copies are deleted again).
    """
    for child in C.getFrame(name).getChildren():
        C.delFrame(child.name)
    C.delFrame(name)


def loadCharacters(C, names):
    """
    Loads characters.g once per copy layer (prefix "c<copy>_") and deletes every piece that is not in names.
    """
    keep = set(names)
    for copy in range(max(getCountsFromNames(names).values())):
        C.addFile(prm.CHARACTERS_FILE, f"c{copy}_")
        for symbol in prm.SYMBOLS:
            if getPieceFrameName(copy, symbol) not in keep:
                deleteFrameAndChildren(C, getPieceFrameName(copy, symbol))


# ------------------------------------------- 3-6. GEOMETRY OF THE ROOM ---------------------------------------------------

def getHalfExtentsWorld(frame):
    """
    Returns half the size of a box along the world axes. This is used for getting wall widths.
    """
    R = frame.getRotationMatrix()
    return np.abs(R) @ (np.array(frame.getSize()[:3]) / 2) # cut the width of the wall to half and turn to world frame


def getFloorTop(C):
    """
    Returns the height of the floor surface
    """
    floor = C.getFrame(prm.FLOOR_FRAME_NAME)
    return floor.getPosition()[2] + floor.getSize()[2] / 2 # add floor width/2 to the z of the floor frame


def getRoomLimits(C):
    """
    Returns the usable floor rectangle for letter placement, we ignore the table and the bases for now.
    """
    floor = C.getFrame(prm.FLOOR_FRAME_NAME)
    fx, fy = floor.getPosition()[:2] # floor x and y positions
    sx, sy = floor.getSize()[:2]     # floor sizes x and y
    x_min, x_max, y_min, y_max = fx - sx / 2, fx + sx / 2, fy - sy / 2, fy + sy / 2 # add and remove size/2 to the center along each axis

    for name in prm.WALL_FRAME_NAMES:   # for each wall
        wall = C.getFrame(name)
        e = getHalfExtentsWorld(wall)   # get walls half-width in world axes
        c = wall.getPosition()          # get walls position in world axes
        if e[0] < e[1]:                     # if the wall is thin in the x direction, remove the width from x
            if c[0] > fx:                   # if wall position in x is greater than floor position in x:
                x_max = min(x_max, c[0] - e[0]) # remove the wall width/2 from the wall position
            else:
                x_min = max(x_min, c[0] + e[0]) # if on the other side, add since its negative
        else:                               # if the wall is thin in the y direction, remove the width from y
            if c[1] > fy:                   # same logic as above
                y_max = min(y_max, c[1] - e[1])
            else:
                y_min = max(y_min, c[1] + e[1])
    return x_min, x_max, y_min, y_max


def getKeepOutBoxes(C):
    """
    Returns the boxes to keep the letters out of, so tables and bases.
    """
    boxes = []
    for name in prm.TABLE_FRAME_NAMES + prm.BASE_FRAME_NAMES: # list of table and base frame names
        frame = C.getFrame(name)
        e = getHalfExtentsWorld(frame)
        c = frame.getPosition()
        boxes.append((c[:2] - e[:2], c[:2] + e[:2]))
    return boxes # list of horizontal boxes to keep out of


# ------------------------------------------- 7-8. ONE PIECE --------------------------------------------------------------

def getOutsideKeepOut(x, y, boxes):
    """
    Returns the boolean value for whether a piece is far enough from tables and bases
    """
    p = np.array([x, y]) # letter position
    for lo, hi in boxes: # for box limits to keep out of
        closest = np.clip(p, lo, hi)        # nearest point of the box to the centre
        if np.linalg.norm(p - closest) < prm.LETTER_RADIUS + prm.TABLE_MARGIN: # if magnitude is smaller than letter and table clearence margin
            return False
    return True


def getOutlinePoints(C, name):
    """
    Returns the array of 2D points covering a symbol's outline
    """
    step = prm.OUTLINE_SAMPLE_STEP
    pts = []
    for stroke in C.getFrame(name).getChildren(): # get symbol and child frames
        if stroke.getShapeType() != ry.ST.ssBox:  # if something other than a ssbox is used, ignore it
            continue
        L, W = stroke.getSize()[:2]               # read length and width of a frame
        cx, cy = stroke.getRelativePosition()[:2] # get the angle about z
        q = stroke.getRelativeQuaternion()        # rotation about only z
        a = 2 * np.arctan2(q[3], q[0])
        for u in np.arange(-L / 2, L / 2 + 1e-9, step):
            for v in np.arange(-W / 2, W / 2 + 1e-9, step):
                pts.append([cx + u * np.cos(a) - v * np.sin(a), cy + u * np.sin(a) + v * np.cos(a)]) # geometrical position of the current point
    return np.array(pts)


def getYawPose(x, y, z, yaw):
    """We need to define 7 numbers for setting poses in RAI, so you convert the yaw and position to quarternions"""
    return [x, y, z, np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]



# ------------------------------------------- 9. SCATTERED PIECES (WITH STACKING) ----------------------------------------

def getWallSpot(rng, x_min, x_max, y_min, y_max):
    """
    Returns a random floor point whose distance to one (random) wall is between LETTER_RADIUS and WALL_NEAR.
    """
    r, along = prm.LETTER_RADIUS, rng.uniform(0, 1)
    d = rng.uniform(prm.LETTER_RADIUS, prm.WALL_NEAR)
    side = rng.integers(4)
    if side == 0:
        return x_min + d, y_min + r + along * (y_max - y_min - 2 * r)
    if side == 1:
        return x_max - d, y_min + r + along * (y_max - y_min - 2 * r)
    if side == 2:
        return x_min + r + along * (x_max - x_min - 2 * r), y_min + d
    return x_min + r + along * (x_max - x_min - 2 * r), y_max - d


def placePieces(C, names, rng, floor_z, pile_centres):
    """
    Places the scattered pieces at random allowed positions with random yaw: a share WALL_SHARE close to a wall
    (getWallSpot), the others anywhere; never closer than PILE_KEEP_OUT to a pile centre. Two pieces that overlap are
    placed on top of each other (height map of 1 cm cells). Returns the number of stacked pieces.
    """
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    boxes = getKeepOutBoxes(C)
    r = prm.LETTER_RADIUS
    cell = prm.HEIGHT_MAP_CELL
    height_map = {}                                 # 1 cm cell -> height of the top of what lies there
    n_stacked = 0
    for i, name in enumerate(names):
        near_wall = i < round(prm.WALL_SHARE * len(names))     # names come shuffled: the first ones go to the walls
        for _ in range(prm.MAX_PLACEMENT_ATTEMPTS):
            if near_wall:
                x, y = getWallSpot(rng, x_min, x_max, y_min, y_max)
            else:
                x, y = rng.uniform([x_min + r, y_min + r], [x_max - r, y_max - r])
            far_from_piles = all(np.hypot(x - c[0], y - c[1]) > prm.PILE_KEEP_OUT for c in pile_centres)
            if getOutsideKeepOut(x, y, boxes) and far_from_piles:
                break
        else:
            raise RuntimeError(f"no free spot for {name}")
        yaw = rng.uniform(-np.pi, np.pi)
        Rz = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
        pts = getOutlinePoints(C, name) @ Rz.T + [x, y]                      # the piece's outline on the floor
        cells = {(int(np.floor(px / cell)), int(np.floor(py / cell))) for px, py in pts}
        z = max([floor_z] + [height_map[c] for c in cells if c in height_map])   # rest on the highest thing below
        n_stacked += z > floor_z
        for c in cells:
            height_map[c] = z + prm.PIECE_THICKNESS
        C.getFrame(name).setPose(getYawPose(x, y, z + prm.PLACEMENT_LIFT, yaw))
    return n_stacked


# ------------------------------------------- 10. PILES -------------------------------------------------------------------

def getPileCentres(C, rng, n):
    """
    Returns n pile centres: random floor points PILE_ZONE_GAP apart, whose whole zone (PILE_ZONE_RADIUS) is inside the
    room and away from tables and bases.
    """
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    boxes = getKeepOutBoxes(C)
    r = prm.PILE_ZONE_RADIUS + prm.LETTER_RADIUS
    centres = []
    for _ in range(prm.MAX_PLACEMENT_ATTEMPTS):
        c = rng.uniform([x_min + r, y_min + r], [x_max - r, y_max - r])
        ring = [c + prm.PILE_ZONE_RADIUS * np.array([np.cos(a), np.sin(a)]) for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
        if all(getOutsideKeepOut(p[0], p[1], boxes) for p in [c] + ring) and \
                all(np.linalg.norm(c - o) > prm.PILE_ZONE_GAP for o in centres):
            centres.append(c)
            if len(centres) == n:
                return centres
    raise RuntimeError(f"no room for {n} piles")


def getTiltedYawQuaternion(yaw, tilt, axis):
    """
    Returns the quaternion (w, x, y, z) of a piece turned by yaw about the vertical, then tilted by `tilt` about the
    horizontal direction at angle `axis`.
    """
    w1, v1 = np.cos(tilt / 2), np.sin(tilt / 2) * np.array([np.cos(axis), np.sin(axis), 0.])   # tilt
    w2, v2 = np.cos(yaw / 2), np.array([0., 0., np.sin(yaw / 2)])                            # yaw
    return np.r_[w1 * w2 - v1 @ v2, w1 * v2 + w2 * v1 + np.cross(v1, v2)]                   # tilt * yaw


def placePilePieces(C, names, rng, floor_z):
    """
    Spreads the pieces over PILE_ZONES piles: each pile is a tower of pieces one above the other (PILE_LAYER_GAP
    apart), each at a random spot within PILE_ZONE_RADIUS of its centre, with a random yaw and a tilt up to
    PILE_MAX_TILT_DEG. When PhysX lets them fall they land on each other, lean and cover each other.
    Returns the pile centres.
    """
    centres = getPileCentres(C, rng, prm.PILE_ZONES)
    height = [0] * len(centres)                             # pieces already dropped on each pile
    for name in names:
        k = int(np.argmin(height))                          # the lowest pile gets the next piece
        a, d = rng.uniform(0, 2 * np.pi), prm.PILE_ZONE_RADIUS * np.sqrt(rng.uniform())   # uniform in the disc
        x, y = centres[k] + d * np.array([np.cos(a), np.sin(a)])
        z = floor_z + 0.002 + height[k] * (prm.PIECE_THICKNESS + prm.PILE_LAYER_GAP)
        q = getTiltedYawQuaternion(rng.uniform(-np.pi, np.pi), np.radians(rng.uniform(0, prm.PILE_MAX_TILT_DEG)),
                                   rng.uniform(0, 2 * np.pi))
        C.getFrame(name).setPosition([x, y, z]).setQuaternion(q)
        height[k] += 1
    return centres


# ------------------------------------------- 11. SETTLING WITH PHYSICS ---------------------------------------------------

def settlePieces(C, names, obstacles=prm.SETTLE_OBSTACLE_NAMES, duration=prm.SETTLE_DURATION,
                 drop=prm.SETTLE_DROP_HEIGHT):
    """
    Lets PhysX settle the named pieces and copies their poses back into C. A separate config holds only the obstacles
    (the fixed frames the pieces can hit; motion/ leaves the robot bases out) and these pieces. Every piece starts
    `drop` higher than it is now (scene building: they fall into place; after a put-down motion/ uses 0, so pieces
    that already lie still do not move). Returns the largest speed over the last SETTLE_CHECK_WINDOW seconds.
    Pieces NOT in names (e.g. one held by a gripper) are not touched.
    """
    S = ry.Config()
    for obstacle in obstacles:
        f = C.getFrame(obstacle)
        S.addFrame(obstacle).setShape(f.getShapeType(), f.getSize()).setPose(f.getPose()).setContact(1)
    loadCharacters(S, names)
    for name in names:
        pose = C.getFrame(name).getPose()
        pose[2] += drop
        S.getFrame(name).setPose(pose)
    sim = ry.Simulation(S, ry.SimulationEngine.physx, verbose=0)
    tau = prm.SETTLE_TIME_STEP
    steps = int(duration / tau)
    check_step = steps - int(prm.SETTLE_CHECK_WINDOW / tau)
    for k in range(steps):
        sim.step([], tau, ry.ControlMode.none)              # no motor commands: only gravity and contacts
        if k == check_step:
            before = np.array([S.getFrame(n).getPosition() for n in names])
    after = np.array([S.getFrame(n).getPosition() for n in names])
    max_speed = np.linalg.norm(after - before, axis=1).max() / prm.SETTLE_CHECK_WINDOW
    for name in names:
        C.getFrame(name).setPose(S.getFrame(name).getPose())
    return max_speed


# ------------------------------------------- 12. CAMERAS -----------------------------------------------------------------

def getCameraAttributes(kind):
    """
    Returns the camera attributes RAI expects for a "mast" or "wrist" camera: focal length (as a fraction of the image
    height), image size in pixels and the depth range in meters.
    """
    if kind == "mast":
        return {"focalLength": prm.MAST_FOCAL_FRACTION, "width": prm.MAST_WIDTH_PX,
                "height": prm.MAST_HEIGHT_PX, "zRange": [prm.MAST_NEAR, prm.MAST_FAR]}
    if kind == "wrist":
        return {"focalLength": prm.WRIST_FOCAL_FRACTION, "width": prm.WRIST_WIDTH_PX,
                "height": prm.WRIST_HEIGHT_PX, "zRange": [prm.WRIST_NEAR, prm.WRIST_FAR]}
    raise ValueError(f"unknown camera kind '{kind}' (use 'mast' or 'wrist')")


def addCamera(C, name, parent, offset, quaternion, attributes):
    """
    Adds one camera frame to the scene. parent = frame it moves with (None: fixed in the world); offset and quaternion
    are relative to that parent. The small marker only makes it visible in the viewer. Returns the frame name.
    """
    if parent is not None:
        frame = C.addFrame(name, parent)
        frame.setRelativePosition(offset).setRelativeQuaternion(quaternion)
    else:                                   # no parent: offset and quaternion are world values
        frame = C.addFrame(name)
        frame.setPosition(offset).setQuaternion(quaternion)
    frame.setShape(ry.ST.marker, [prm.CAMERA_MARKER_SIZE]).setAttributes(attributes)
    return name


def addMastCameras(C):
    """
    One mast camera per robot: child of its mobile base, MAST_OFFSET above it, looking straight down.
    """
    return [addCamera(C, prm.MAST_CAMERA_PATTERN.format(robot=r), prm.ROBOT_BASE[r],
                      prm.MAST_OFFSET, prm.LOOK_DOWN_QUATERNION, getCameraAttributes("mast"))
            for r in prm.ROBOT_NAMES]


def addWristCameras(C):
    """
    One wrist camera per robot: child of its gripper, so it moves with the arm (looks down when the gripper does).
    """
    return [addCamera(C, prm.WRIST_CAMERA_PATTERN.format(robot=r), prm.GRIPPER_FRAME_PATTERN.format(robot=r),
                      prm.WRIST_OFFSET, prm.LOOK_DOWN_QUATERNION, getCameraAttributes("wrist"))
            for r in prm.ROBOT_NAMES]


def getLookDownQuaternion(heading):
    """
    Quaternion (w, x, y, z) of a camera looking straight down, turned by `heading` about the vertical.
    It is the turn about z (cos h/2, 0, 0, sin h/2) times the 180 deg flip about x (0, 1, 0, 0).
    """
    return [0., np.cos(heading / 2), np.sin(heading / 2), 0.]


def placeTestCamera(C, x, y, height, heading, floor_z):
    """
    Moves the free test camera to `height` above the floor over (x, y), looking down, turned by `heading`.
    """
    C.getFrame(prm.TEST_CAMERA_NAME).setPosition([x, y, floor_z + height]).setQuaternion(getLookDownQuaternion(heading))


def addTestCamera(C, floor_z, kind=prm.TEST_CAMERA_KIND):
    """
    One free camera (no parent) with mast or wrist intrinsics, for looking at any spot without moving a robot.
    Starts over the floor centre at TEST_CAMERA_HEIGHT.
    """
    addCamera(C, prm.TEST_CAMERA_NAME, None, [0., 0., 0.], prm.LOOK_DOWN_QUATERNION, getCameraAttributes(kind))
    fx, fy = C.getFrame(prm.FLOOR_FRAME_NAME).getPosition()[:2]
    placeTestCamera(C, fx, fy, prm.TEST_CAMERA_HEIGHT, 0., floor_z)
    return prm.TEST_CAMERA_NAME


def addCameras(C, floor_z, cameras):
    """
    Adds the chosen cameras ("mast", "wrist", "test") and returns the names of all camera frames added.
    """
    names = []
    if "mast" in cameras:
        names += addMastCameras(C)
    if "wrist" in cameras:
        names += addWristCameras(C)
    if "test" in cameras:
        names.append(addTestCamera(C, floor_z))
    return names


# ------------------------------------------- 13. THE TASK SCENE ----------------------------------------------------------

def buildScene(word=prm.WORD, seed=prm.RANDOM_SEED, cameras=("mast", "wrist", "test"), verbose=True):
    """
    Room + robots + the task pieces (getTaskCounts): PILE_SHARE of them in piles, the rest scattered (some near the
    walls), settled with PhysX, + cameras. Returns (C, piece_names, floor_top, camera_names).
    """
    C = ry.Config()
    C.addFile(prm.SCENE_FILE)
    names = getPieceNames(getTaskCounts(word))
    loadCharacters(C, names)
    floor_z = getFloorTop(C)
    rng = np.random.default_rng(seed)
    order = [names[i] for i in rng.permutation(len(names))]
    n_pile = int(round(prm.PILE_SHARE * len(names)))
    centres = placePilePieces(C, order[:n_pile], rng, floor_z)
    n_stacked = placePieces(C, order[n_pile:], rng, floor_z, centres)
    max_speed = settlePieces(C, names, duration=prm.PILE_SETTLE_DURATION)
    camera_names = addCameras(C, floor_z, cameras)
    if verbose:
        print(f"{len(names)} pieces: {n_pile} in {len(centres)} piles, {len(names) - n_pile} scattered "
              f"({round(prm.WALL_SHARE * (len(names) - n_pile))} near walls, {n_stacked} landed on another); "
              f"settled: max speed {max_speed:.4f} m/s")
    return C, names, floor_z, camera_names


# ------------------------------------------- 14. RUN DIRECTLY ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    C, names, floor_z, camera_names = buildScene(sys.argv[1] if len(sys.argv) > 1 else prm.WORD)
    print("cameras:", camera_names)
    C.view(True)
