"""
Robot test: one robot uses THIS perception package to find pieces, look at them closely and grasp them, with basic
motions, so you can watch in the viewer how well perception works in the scene.

    python3 perception/robot_test.py                         CNN reader, seed 0, viewer
    python3 perception/robot_test.py --reader template --seed 3 --targets 8
    python3 perception/robot_test.py --headless              no viewer (prints the results only)

With --piles N (default TEST_PILES), N extra piles of PILE_SIZE pieces are made near the robot first and settled with
PhysX, to see how perception does on pieces lying on others. A piece taken off a pile is put down beside it (upright),
so the piece below becomes visible to the next mast scan.

For each target:
    1. mast scan          readPicture with the mast camera; take the closest trusted read (conf >= CONF_ACT)
    2. drive              put the base PICK_DISTANCE from the read's grasp point, facing it (straight line, no path
                          planning)
    3. wrist re-read      KOMO: gripper above the piece, looking down; readPicture with the wrist camera
    4. grasp              KOMO: gripper at the grasp point of the READ pose (symbol, xy, yaw); this is where a wrong
                          read shows: the gripper misses the stroke
    5. turn upright       if the grasp holds, the piece is attached, turned by minus the read yaw and put down again
                          (in place, or beside the pile if it lay on another piece), then PhysX lets it settle; every
                          handled piece should end upright (yaw 0) in the viewer; what is left is the error
A marker is left at every read pose: green for a right read, red for a wrong one.

Kept basic on purpose: robot motions are kinematic, no collision checks, no path planning, grasping is attach(); only
the pieces get physics (settling after the piles are made and after every put-down).
The ground truth is used only to score the reads and to decide whether a grasp holds.
"""
import os
import sys
import time
import argparse
import numpy as np
import robotic as ry #type: ignore

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parameters as prm
from scene_builder import buildScene, settlePieces, getKeepOutBoxes, getOutsideKeepOut, getRoomLimits
from templates import loadTemplates
from reader import readPicture
from camera import takePicture
from classify_template import classifyTemplate
from ground_truth import getTruth
from confidence import wrapAngle


# ---------------------------------------------------------------- the robot's joints

def getJointIndices(C, robot):
    """
    Returns (base indices, arm indices) of the robot's joints in C.getJointState(): base x, y, yaw and 7 arm joints.
    """
    names = C.getJointNames()
    base = prm.ROBOT_BASE[robot]
    base_idx = [names.index(f"{base}:{i}") for i in range(3)]
    arm_idx = [names.index(f"{robot}_panda_joint{i}") for i in range(1, 8)]
    return base_idx, arm_idx


def getBaseOrigin(C, robot):
    """
    Returns the xy the base joints are measured from (base joint x, y = base position - origin).
    """
    i = prm.ROBOT_NAMES.index(robot) + 1
    return C.getFrame(prm.BASE_ORIGIN_PATTERN.format(i=i)).getPosition()[:2]


def moveJoints(C, idx, target, show):
    """
    Moves the joints idx to target in a straight line in joint space, drawing every step if show.
    """
    q0 = C.getJointState()
    q1 = q0.copy()
    q1[idx] = target
    steps = prm.ANIMATION_STEPS if show else 1
    for s in range(1, steps + 1):
        C.setJointState(q0 + (q1 - q0) * s / steps)
        if show:
            C.view(False)
            time.sleep(prm.ANIMATION_STEP_TIME)


# ---------------------------------------------------------------- motions

def getArmIK(C, robot, position, closing_dir, q_start):
    """
    KOMO, one time slice: arm joints that put the gripper at `position`, pointing down, closing axis along
    closing_dir (xy). The base stays where it is. Returns the 7 arm joints or None.
    """
    Cp = ry.Config()
    Cp.addConfigurationCopy(C)
    _, arm_idx = getJointIndices(Cp, robot)
    q = Cp.getJointState()
    q[arm_idx] = q_start
    Cp.setJointState(q)
    Cp.selectJoints([f"{robot}_panda_joint{i}" for i in range(1, 8)])
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    k = ry.KOMO(Cp, 1, 1, 0, False)
    k.addControlObjective([], 0, 1e-1)
    k.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq, [1e1])
    k.addObjective([], ry.FS.position, [gripper], ry.OT.eq, [1e1], list(position))
    k.addObjective([], ry.FS.vectorZ, [gripper], ry.OT.eq, [1e1], [0., 0., 1.])
    k.addObjective([], ry.FS.vectorX, [gripper], ry.OT.eq, [1e1], [closing_dir[0], closing_dir[1], 0.])
    ret = ry.NLP_Solver(k.nlp(), verbose=0).setOptions(stopTolerance=1e-3).solve()
    if ret.eq > prm.IK_TOLERANCE or ret.ineq > prm.IK_TOLERANCE:
        return None
    return k.getPath()[0].copy()


def getTopHeightAt(view, C, camera, xy, read):
    """
    Returns the height of the piece's top face at xy, measured in the camera's point cloud: the median height of the
    points within GRASP_TOL_XY of xy and no higher than the read's top. A piece leaning on another one is not level,
    so read["z_top"] (its highest part) can be centimetres above the grasp point. Falls back to read["z_top"].
    """
    _, points, valid, _ = takePicture(view, C, camera)
    near = valid & (np.linalg.norm(points[:, :2] - xy, axis=1) < prm.GRASP_TOL_XY) & (points[:, 2] < read["z_top"] + .005)
    return float(np.median(points[near, 2])) if near.sum() >= 3 else read["z_top"]


def getGrasp(read, templates):
    """
    Returns (grasp point xy, closing angle) in the room for a read: the symbol's grasp marker moved by the read pose.
    """
    k = templates["symbols"].index(read["symbol"])
    g_xy, g_angle = templates["grasp"][k]
    c, s = np.cos(read["yaw"]), np.sin(read["yaw"])
    return np.asarray(read["xy"]) + np.array([[c, -s], [s, c]]) @ np.asarray(g_xy), read["yaw"] + g_angle


def driveTo(C, robot, grasp_xy, show):
    """
    Drives the base (arm at home) to a spot PICK_DISTANCE from grasp_xy facing it, trying spots around it, the first
    one on the line from the current base position. Returns True if the gripper can reach above the piece from there.
    """
    base_idx, arm_idx = getJointIndices(C, robot)
    origin = getBaseOrigin(C, robot)
    here = C.getJointState()[base_idx[:2]] + origin
    a0 = np.arctan2(here[1] - grasp_xy[1], here[0] - grasp_xy[0])
    turns = [0] + [s * j for j in range(1, prm.PICK_TRIES) for s in (1, -1)]       # 0, +1, -1, +2, -2, ... steps
    for a in a0 + np.radians(360 / prm.PICK_TRIES) * np.array(turns[:prm.PICK_TRIES]):
        b = grasp_xy + prm.PICK_DISTANCE * np.array([np.cos(a), np.sin(a)])
        phi = a + np.pi                                     # face the piece
        q = C.getJointState()
        q[base_idx] = [b[0] - origin[0], b[1] - origin[1], phi]
        q[arm_idx] = prm.ARM_HOME
        Cp = ry.Config()
        Cp.addConfigurationCopy(C)
        Cp.setJointState(q)
        if getArmIK(Cp, robot, [grasp_xy[0], grasp_xy[1], 0.3], [np.cos(phi), np.sin(phi)], prm.ARM_HOME) is None:
            continue
        moveJoints(C, arm_idx, prm.ARM_HOME, show)
        moveJoints(C, base_idx, q[base_idx], show)
        return True
    return False


# ---------------------------------------------------------------- scoring with the ground truth

def getTruePiece(read, truth):
    """
    Returns the true piece a read belongs to: within MATCH_DISTANCE in xy and, among those, the one whose top face is
    closest in height (two pieces of a pile have nearly the same xy, the height tells them apart). None if none.
    """
    near = [p for p in truth if np.linalg.norm(p["xy"] - read["xy"]) < prm.MATCH_DISTANCE]
    if not near:
        return None
    return min(near, key=lambda p: abs(p["z"] + prm.PIECE_THICKNESS - read["z_top"]))


def scoreRead(read, truth, templates):
    """
    Returns (true piece or None, symbol right, xy error m, yaw error deg); a half turn is no error for a glyph that
    looks the same upside down.
    """
    piece = getTruePiece(read, truth)
    if piece is None:
        return None, False, np.nan, np.nan
    d = abs(wrapAngle(read["yaw"] - piece["yaw"]))
    if templates["sym180"][piece["k"]]:
        d = min(d, np.pi - d)
    return piece, read["symbol"] == piece["symbol"], float(np.linalg.norm(read["xy"] - piece["xy"])), float(np.degrees(d))


def graspHolds(C, grasp_xy, closing, z, piece, templates):
    """
    Returns (holds, distance to the true grasp point, closing axis error deg, height error): the gripper holds the piece if it
    closes near the TRUE grasp point, with the true closing axis (either direction), at the right height.
    """
    true_xy, true_closing = getGrasp({"symbol": piece["symbol"], "xy": piece["xy"], "yaw": piece["yaw"]}, templates)
    d = float(np.linalg.norm(grasp_xy - true_xy))
    a = abs(wrapAngle(closing - true_closing))
    a = float(np.degrees(min(a, np.pi - a)))
    k = templates["symbols"].index(piece["symbol"])
    frame = C.getFrame(piece["name"])                       # top face height at the grasp point (pieces can lean)
    R = frame.getRotationMatrix()
    top = frame.getPosition() + R @ np.r_[templates["grasp"][k][0], prm.PIECE_THICKNESS]
    true_z = top[2] - prm.ORIGIN_BELOW_TOP + prm.GRASP_ABOVE_ORIGIN
    dz = float(z - true_z)
    ok = d < prm.GRASP_TOL_XY and a < prm.GRASP_TOL_ANGLE_DEG and abs(dz) < prm.GRASP_TOL_Z
    return ok, d, a, dz


def addMarker(C, i, read, right):
    """
    Leaves a marker (axes) at a read pose: green if the read was right, red if wrong.
    """
    yaw = read["yaw"]
    C.addFrame(f"read_{i}").setShape(ry.ST.marker, [.12]).setPosition([*read["xy"], read["z_top"] + .01]) \
        .setQuaternion([np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]).setColor([0, 1, 0] if right else [1, 0, 0])


# ---------------------------------------------------------------- putting a piece down

def getSetAsideSpot(C, robot, grasp_xy, z_floor, closing, reads):
    """
    Returns a floor spot SET_ASIDE_DISTANCE from the pile for the grasp point, reachable from where the base stands,
    inside the room, away from tables and bases, and as far as possible from every piece the mast saw. None if none.
    """
    _, arm_idx = getJointIndices(C, robot)
    x_min, x_max, y_min, y_max = getRoomLimits(C)
    boxes = getKeepOutBoxes(C)
    seen = np.array([r["xy"] for r in reads]) if reads else np.zeros((0, 2))
    spots = []
    for a in np.linspace(-np.pi, np.pi, prm.SET_ASIDE_TRIES, endpoint=False):
        p = grasp_xy + prm.SET_ASIDE_DISTANCE * np.array([np.cos(a), np.sin(a)])
        if not (x_min < p[0] < x_max and y_min < p[1] < y_max and getOutsideKeepOut(p[0], p[1], boxes)):
            continue
        clearance = np.min(np.linalg.norm(seen - p, axis=1)) if len(seen) else 1.
        spots.append((clearance, p))
    for _, p in sorted(spots, key=lambda x: -x[0]):
        if getArmIK(C, robot, [*p, z_floor + prm.PRE_GRASP_LIFT], [np.cos(closing), np.sin(closing)],
                    C.getJointState()[arm_idx]) is not None:
            return p
    return None


def putDown(C, robot, piece_name, place_xy, z, hold, turn, show):
    """
    The gripper holds the piece (lifted), closing axis at angle `hold`. Carries it so that the grasp point ends at
    place_xy, turned by `turn` about the grasp point, and puts it down at height z. The last arm joint cannot turn more
    than ~2.9 rad, so if the whole turn has no IK solution: turn half, put it down, grasp it again from the other side
    (same grasp, gripper turned by 180 deg) and turn the rest. Returns True if done (the piece is down, still attached).
    """
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    _, arm_idx = getJointIndices(C, robot)

    def goDown(angle, now):
        """IK above and at place_xy for closing angle `angle`, the gripper now at angle `now`. Turning the gripper
        about the vertical is (nearly) turning the last arm joint, so KOMO starts from the last joint turned by the
        difference, one way or the other."""
        d = [np.cos(angle), np.sin(angle)]
        for sign in (1., -1.):
            q0 = C.getJointState()[arm_idx]
            q0[6] = np.clip(q0[6] + sign * wrapAngle(angle - now), -2.8, 2.8)
            q_up = getArmIK(C, robot, [*place_xy, z + prm.PRE_GRASP_LIFT], d, q0)
            q_down = None if q_up is None else getArmIK(C, robot, [*place_xy, z], d, q_up)
            if q_down is not None:
                return q_up, q_down
        return None

    for _ in range(3):
        qs = goDown(hold + turn, hold)
        if qs is not None:
            moveJoints(C, arm_idx, qs[0], show)
            moveJoints(C, arm_idx, qs[1], show)
            return True
        half = goDown(hold + turn / 2, hold)
        if half is None:
            return False
        moveJoints(C, arm_idx, half[0], show)
        moveJoints(C, arm_idx, half[1], show)
        C.attach(prm.FLOOR_FRAME_NAME, piece_name)          # let go
        moveJoints(C, arm_idx, half[0], show)
        now = hold + turn / 2
        hold, turn = now + np.pi, turn / 2                  # grasp again from the other side
        again = goDown(hold, now)
        if again is None:
            return False
        moveJoints(C, arm_idx, again[0], show)
        moveJoints(C, arm_idx, again[1], show)
        C.attach(gripper, piece_name)
        moveJoints(C, arm_idx, again[0], show)
    return False


# ---------------------------------------------------------------- one target

def handleTarget(C, view, robot, target, reads, names, templates, classifier, floor_z, i, show):
    """
    Goes to one mast read: drive, wrist re-read, grasp at the read pose; if the grasp holds, put the piece down
    upright (in place, or beside the pile if it lay on another piece) and let PhysX settle it.
    Returns (result row for the summary, where the piece is now in xy).
    """
    base_idx, arm_idx = getJointIndices(C, robot)
    gripper = prm.GRIPPER_FRAME_PATTERN.format(robot=robot)
    row = {"mast": target["symbol"], "mast_conf": target["conf"], "on_pile": bool(target["stacked"])}
    if not driveTo(C, robot, getGrasp(target, templates)[0], show):
        return {**row, "result": "no base spot"}, target["xy"]

    # wrist re-read from above the piece
    phi = C.getJointState()[base_idx[2]]
    above = [*target["xy"], target["z_top"] + prm.WRIST_VIEW_HEIGHT]
    q_view = getArmIK(C, robot, above, [np.cos(phi + np.pi / 2), np.sin(phi + np.pi / 2)], prm.ARM_HOME)
    read, row["source"] = target, "mast"
    camera = prm.MAST_CAMERA_PATTERN.format(robot=robot)
    if q_view is not None:
        moveJoints(C, arm_idx, q_view, show)
        near = [r for r in readPicture(view, C, prm.WRIST_CAMERA_PATTERN.format(robot=robot), templates, floor_z, classifier)
                if np.linalg.norm(r["xy"] - target["xy"]) < prm.WRIST_MATCH_DISTANCE]
        best = max(near, key=lambda r: r["conf"]) if near else None
        if best is not None and best["conf"] >= prm.CONF_ACCEPT:
            read, row["source"] = best, "wrist"
            camera = prm.WRIST_CAMERA_PATTERN.format(robot=robot)
    row.update(read=read["symbol"], conf=read["conf"])

    piece, right, xy_err, yaw_err = scoreRead(read, getTruth(C, names), templates)
    row.update(true=piece["symbol"] if piece else "-", right=right, xy_err=xy_err, yaw_err=yaw_err,
               name=piece["name"] if piece else None)
    addMarker(C, i, read, right)
    if piece is None:
        moveJoints(C, arm_idx, prm.ARM_HOME, show)
        return {**row, "result": "no piece there"}, read["xy"]

    # grasp at the READ pose (the gripper is symmetric: two ways to hold the same grasp)
    grasp_xy, closing = getGrasp(read, templates)
    z = getTopHeightAt(view, C, camera, grasp_xy, read) - prm.ORIGIN_BELOW_TOP + prm.GRASP_ABOVE_ORIGIN
    for flip in (0., np.pi):
        d = [np.cos(closing + flip), np.sin(closing + flip)]
        q_pre = getArmIK(C, robot, [*grasp_xy, z + prm.PRE_GRASP_LIFT], d, C.getJointState()[arm_idx])
        q_grasp = None if q_pre is None else getArmIK(C, robot, [*grasp_xy, z], d, q_pre)
        if q_grasp is not None:
            break
    if q_grasp is None:
        moveJoints(C, arm_idx, prm.ARM_HOME, show)
        return {**row, "result": "no grasp IK"}, read["xy"]
    moveJoints(C, arm_idx, q_pre, show)
    moveJoints(C, arm_idx, q_grasp, show)
    holds, row["grasp_err"], row["grasp_angle_err"], row["z_err"] = graspHolds(C, grasp_xy, closing, z, piece, templates)
    if not holds:
        moveJoints(C, arm_idx, q_pre, show)
        moveJoints(C, arm_idx, prm.ARM_HOME, show)
        return {**row, "result": "grasp misses"}, read["xy"]

    # lift; put down upright: in place, or beside the pile if it lay on another piece
    C.attach(gripper, piece["name"])
    moveJoints(C, arm_idx, q_pre, show)
    place_xy, place_z, result = grasp_xy, z, "turned upright"
    if read["stacked"]:
        z_floor = floor_z + prm.PIECE_THICKNESS - prm.ORIGIN_BELOW_TOP + prm.GRASP_ABOVE_ORIGIN + .005
        spot = getSetAsideSpot(C, robot, grasp_xy, z_floor, closing + flip, reads)
        if spot is not None:
            place_xy, place_z, result = spot, z_floor, "set aside upright"
    done = putDown(C, robot, piece["name"], place_xy, place_z, closing + flip, -read["yaw"], show)
    if not done and result == "set aside upright":          # no way to turn it there: try back on the pile
        place_xy, place_z, result = grasp_xy, z, "turned upright"
        done = putDown(C, robot, piece["name"], place_xy, place_z, closing + flip, -read["yaw"], show)
    if not done:
        result = "held, could not put down"                 # let go where it is: PhysX drops it
    C.attach(prm.FLOOR_FRAME_NAME, piece["name"])
    moveJoints(C, arm_idx, prm.ARM_HOME, show)
    settlePieces(C, names, prm.STATIC_OBSTACLE_NAMES, drop=0.)  # PhysX: the piece (and the pile) come to rest
    after = getTruth(C, [piece["name"]])[0]
    row["final_yaw"] = float(np.degrees(wrapAngle(after["yaw"])))
    if show:
        C.view(False)
    return {**row, "result": result}, after["xy"]


# ---------------------------------------------------------------- main

def getNextTarget(C, view, robot, templates, classifier, floor_z, visited, uncovered):
    """
    Mast scan; returns (the next target or None, all reads). Candidates: trusted reads not near a visited spot.
    Piles go first: a read of a piece lying on another, or of a piece where one was just taken off (uncovered);
    otherwise the closest to the base.
    """
    reads = readPicture(view, C, prm.MAST_CAMERA_PATTERN.format(robot=robot), templates, floor_z, classifier)
    base = C.getFrame(prm.ROBOT_BASE[robot]).getPosition()[:2]
    ok = [r for r in reads if r["conf"] >= prm.CONF_ACT
          and all(np.linalg.norm(r["xy"] - v) > prm.VISITED_DISTANCE for v in visited)]
    def getPriority(r):
        on_pile = r["stacked"] or any(np.linalg.norm(r["xy"] - u) < prm.VISITED_DISTANCE for u in uncovered)
        return (not on_pile, np.linalg.norm(r["xy"] - base))
    return (min(ok, key=getPriority) if ok else None), reads


def printSummary(rows):
    print(f"\n{'#':>2s} {'pile':>5s} {'mast':>4s} {'read':>4s} {'true':>4s} {'from':>5s} {'conf':>5s} {'xy err':>7s} "
          f"{'yaw err':>8s} {'grasp err':>9s} {'z err':>6s} {'final yaw':>9s}  result")
    for i, r in enumerate(rows):
        f = lambda key, fmt: format(r[key], fmt) if key in r and r[key] == r[key] else "-"
        pile = "top" if r["on_pile"] else ""
        print(f"{i:2d} {pile:>5s} {r['mast']:>4s} {r.get('read', '-'):>4s} {r.get('true', '-'):>4s} "
              f"{r.get('source', '-'):>5s} {f('conf', '5.2f'):>5s} {f('xy_err', '7.3f'):>7s} {f('yaw_err', '8.1f'):>8s} "
              f"{f('grasp_err', '9.3f'):>9s} {f('z_err', '6.3f'):>6s} {f('final_yaw', '9.1f'):>9s}  {r['result']}")
    held = ("turned upright", "set aside upright", "held, could not put down")
    for label, group in (("pile pieces", [r for r in rows if r["on_pile"]]),
                         ("other pieces", [r for r in rows if not r["on_pile"]])):
        if group:
            print(f"{label:12s}: reads right {sum(r.get('right', False) for r in group)}/{len(group)}, "
                  f"grasps that hold {sum(r['result'] in held for r in group)}/{len(group)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", choices=["template", "cnn"], default="cnn")
    ap.add_argument("--seed", type=int, default=prm.RANDOM_SEED)
    ap.add_argument("--targets", type=int, default=prm.N_TARGETS)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    show = not args.headless

    C, names, floor_z, _ = buildScene(prm.WORD, args.seed, verbose=False)
    robot = prm.TEST_ROBOT
    view = ry.CameraView(C)
    templates = loadTemplates()
    if args.reader == "cnn":
        sys.path.insert(0, os.path.join(HERE, "cnn"))
        from classify_cnn import CnnClassifier
        classifier = CnnClassifier()
    else:
        classifier = classifyTemplate
    if show:
        C.view(False, f"robot test: {args.reader} reader, seed {args.seed}")

    rows, visited, uncovered = [], [], []
    for i in range(args.targets):
        target, reads = getNextTarget(C, view, robot, templates, classifier, floor_z, visited, uncovered)
        if target is None:
            print("no trusted read left in view")
            break
        row, now_at = handleTarget(C, view, robot, target, reads, names, templates, classifier, floor_z, i, show)
        visited.append(now_at)                              # where the piece is now (the spot below a pile stays open)
        if row["result"] == "set aside upright":
            uncovered.append(target["xy"])                  # the piece below is next
        rows.append(row)
        print(f"target {i}: {row['result']}")
    printSummary(rows)
    if show:
        C.view(True, "done: green marker = right read, red = wrong (press a key to close)")
