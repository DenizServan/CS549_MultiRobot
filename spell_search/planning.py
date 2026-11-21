# Motion planning for one mobile manipulator.
#   - arm IK with KOMO (one time slice, collisions with tables / bases / the other robot as constraints)
#   - joint-space paths between IK key frames, checked for collisions
#   - base navigation: A* on a 10 cm grid of the room, tables and the other robot as obstacles
#   - choice of base poses for picking a piece from the floor and placing it on a table cell
#   - pieces on the floor as soft obstacles (inflated occupancy with a cost), the pieces that block a
#     path, and a spot within reach to set a cleared piece aside
import heapq
from scipy import ndimage
import numpy as np
import robotic as ry
from config import *
from world import wrap


def T_of(pose7):
    p, q = np.asarray(pose7[:3]), np.asarray(pose7[3:])
    w, x, y, z = q / np.linalg.norm(q)
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                  [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                  [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


class Planner:
    def __init__(self, world):
        self.W = world
        C = world.C
        f = C.getFrame("floor")
        fx, fy = f.getPosition()[:2]
        # room interior (inside the walls), like find_room_limits in place_characters.py
        self.room = np.array([fx - 4.745, fx + 4.745, fy - 4.745, fy + 4.745])
        self.tables = {}
        for t in ("table_left", "table_right"):
            tf = C.getFrame(t)
            self.tables[t] = (tf.getPosition()[:2], np.array(tf.getSize()[:2]) / 2, tf.getPosition()[2] + tf.getSize()[2] / 2)
        self.res = .1
        self.nx = int((self.room[1] - self.room[0]) / self.res) + 1
        self.ny = int((self.room[3] - self.room[2]) / self.res) + 1
        xs = self.room[0] + np.arange(self.nx) * self.res
        ys = self.room[2] + np.arange(self.ny) * self.res
        self.X, self.Y = np.meshgrid(xs, ys, indexing="ij")
        m = BASE_RADIUS + .05
        free = (self.X > self.room[0] + m) & (self.X < self.room[1] - m) & (self.Y > self.room[2] + m) & (self.Y < self.room[3] - m)
        mt = .25 + .04                                  # half base width + margin: a base facing the table may stand close
        # driving past a table, the base turns and its corner (half diagonal .354 m) hit the table
        # (collision monitor). Paths keep BASE_RADIUS + 2 cm from the tables; only a goal (a place pose, where the
        # base faces the table squarely) may lie in the band between the two margins.
        loose, strict = free.copy(), free.copy()
        for c, e, _ in self.tables.values():
            loose &= ~((np.abs(self.X - c[0]) < e[0] + mt) & (np.abs(self.Y - c[1]) < e[1] + mt))
            ms = BASE_RADIUS + .02
            strict &= ~((np.abs(self.X - c[0]) < e[0] + ms) & (np.abs(self.Y - c[1]) < e[1] + ms))
        self.static_free = strict
        self.band = loose & ~strict                     # goal-only cells next to the tables
        self.ik_calls = 0

    # --- arm ----------------------------------------------------------------------------------------
    def ik(self, r, base_pose, pos, xdir, q0=None, held=None):
        """gripper at pos, pointing down (gripper z = world z), closing axis along xdir"""
        self.ik_calls += 1
        W = self.W
        Cp = ry.Config()
        Cp.addConfigurationCopy(W.C)
        q = Cp.getJointState()
        q[W.base_idx[r]] = np.r_[np.asarray(base_pose[:2]) - BASE_ORIGIN[r], base_pose[2]]
        q[W.arm_idx[r]] = HOME if q0 is None else q0
        Cp.setJointState(q)
        Cp.selectJoints(W.arm_joints[r])
        k = ry.KOMO(Cp, 1, 1, 0, True)
        k.addControlObjective([], 0, 1e-1)
        k.addObjective([], ry.FS.jointLimits, [], ry.OT.ineq, [1e1])
        k.addObjective([], ry.FS.position, [f"{r}_gripper"], ry.OT.eq, [1e1], list(pos))
        k.addObjective([], ry.FS.vectorZ, [f"{r}_gripper"], ry.OT.eq, [1e1], [0, 0, 1])
        k.addObjective([], ry.FS.vectorX, [f"{r}_gripper"], ry.OT.eq, [1e1], [xdir[0], xdir[1], 0])
        k.addObjective([], ry.FS.accumulatedCollisions, [], ry.OT.eq, [1e1])
        ret = ry.NLP_Solver(k.nlp(), verbose=0).setOptions(stopTolerance=1e-3).solve()
        if ret.eq > 2e-2 or ret.ineq > 1e-2:
            return None
        return k.getPath()[0].copy()

    def path_ok(self, r, base_pose, qa, qb, n=6):
        """joint-space segment free of collisions (tables, bases, the other robot)?"""
        W = self.W
        Cp = ry.Config()
        Cp.addConfigurationCopy(W.C)
        q = Cp.getJointState()
        q[W.base_idx[r]] = np.r_[np.asarray(base_pose[:2]) - BASE_ORIGIN[r], base_pose[2]]
        for s in np.linspace(0, 1, n):
            q[W.arm_idx[r]] = (1 - s) * qa + s * qb
            Cp.setJointState(q)
            if Cp.eval(ry.FS.accumulatedCollisions, [])[0][0] > 1e-3:
                return False
        return True

    # --- base -------------------------------------------------------------------------------------
    def free_grid(self, others):
        """others: list of (xy, radius) discs the base centre must stay out of"""
        free = self.static_free.copy()
        for c, rad in others:
            free &= (self.X - c[0]) ** 2 + (self.Y - c[1]) ** 2 > rad ** 2
        return free

    def cell(self, xy):
        return (int(round((xy[0] - self.room[0]) / self.res)), int(round((xy[1] - self.room[2]) / self.res)))

    def is_free(self, xy, free):
        i, j = self.cell(xy)
        return 0 <= i < self.nx and 0 <= j < self.ny and free[i, j]

    # optional cost grid (extra cost of entering a cell, in grid steps): pieces as soft obstacles
    def astar(self, start, goal, free, cost=None):
        extra = cost                                    # the name cost is taken below
        s, g = self.cell(start), self.cell(goal)
        # a goal in the band next to a table is allowed (see __init__)
        if not (0 <= g[0] < self.nx and 0 <= g[1] < self.ny and (free[g] or self.band[g])):
            return None
        free = free.copy()
        free[s] = True                                  # we are where we are
        free[g] = True                                  # only the goal cell of the band
        nb = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        h = lambda c: np.hypot(c[0] - g[0], c[1] - g[1])
        openl, came, cost = [(h(s), 0., s)], {s: None}, {s: 0.}
        while openl:
            _, c, cur = heapq.heappop(openl)
            if cur == g:
                break
            if c > cost[cur]:
                continue
            for dx, dy, w in nb:
                n = (cur[0] + dx, cur[1] + dy)
                if 0 <= n[0] < self.nx and 0 <= n[1] < self.ny and free[n]:
                    nc = c + w + (0. if extra is None else extra[n])
                    if nc < cost.get(n, 1e9):
                        cost[n], came[n] = nc, cur
                        heapq.heappush(openl, (nc + h(n), nc, n))
        if g not in came:
            return None
        cells = [g]
        while came[cells[-1]] is not None:
            cells.append(came[cells[-1]])
        pts = [np.array(start[:2])] + [np.array([self.room[0] + i * self.res, self.room[2] + j * self.res]) for i, j in cells[::-1][1:-1]] + [np.array(goal[:2])]
        # shortcut the grid path (line of sight on the free grid)
        out, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            # a shortcut must not cut through costly cells either
            while j > i + 1 and not self.line_free(pts[i], pts[j], free if extra is None else free & (extra <= 0)):
                j -= 1
            out.append(pts[j])
            i = j
        return out

    def line_free(self, a, b, free):
        n = int(np.linalg.norm(b - a) / (self.res / 2)) + 1
        return all(self.is_free(a + (b - a) * s, free) for s in np.linspace(0, 1, n)[1:])

    def path_length(self, pts):
        return sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)) if pts else np.inf

    # --- key frames for one pick and one place --------------------------------------------------------
    # optional cost grid; base poses outside it (not standing on other pieces) are preferred
    def plan_pick(self, r, est, start, free, piece_z, cost=None):
        """est: perception result (symbol, xy, yaw). Returns base pose and arm key frames, or None.
        Tries base poses around the piece (closest first) and both closing directions of the grasp."""
        g_rel, g_ang = self.tpl.grasp[est["symbol"]]
        c, s = np.cos(est["yaw"]), np.sin(est["yaw"])
        gxy = est["xy"] + np.array([[c, -s], [s, c]]) @ g_rel
        psi = est["yaw"] + g_ang
        gz = piece_z + .02
        centre = est["xy"]
        cands = []
        for d in PICK_DIST:
            for a in np.linspace(-np.pi, np.pi, 24, endpoint=False):
                b = gxy + d * np.array([np.cos(a), np.sin(a)])
                if self.is_free(b, free):
                    cands.append((np.linalg.norm(b - start[:2]) + .3 * abs(d - .58) + 5. * self.costly(b, cost), b))
        cands.sort(key=lambda x: x[0])
        for _, b in cands[:10]:
            pts = self.astar(start, b, free, cost)
            if pts is None:
                continue
            phi = np.arctan2(gxy[1] - b[1], gxy[0] - b[0])
            base = np.r_[b, phi]
            view = self.ik(r, base, [centre[0], centre[1], piece_z + .04 + WRIST_VIEW_H],
                           [np.cos(phi + np.pi / 2), np.sin(phi + np.pi / 2)])
            if view is None:
                continue
            for sign in (0, np.pi):
                xd = [np.cos(psi + sign), np.sin(psi + sign)]
                pre = self.ik(r, base, [gxy[0], gxy[1], gz + .15], xd, view)
                if pre is None:
                    continue
                grasp = self.ik(r, base, [gxy[0], gxy[1], gz], xd, pre)
                if grasp is None:
                    continue
                if not (self.path_ok(r, base, HOME, view) and self.path_ok(r, base, view, pre)):
                    continue
                return {"base": base, "path": pts, "view": view, "pre": pre, "grasp": grasp,
                        "gxy": gxy, "gz": gz, "psi": psi + sign}
        return None

    # optional cost grid, as in plan_pick
    def plan_place(self, r, table, cell_xy, piece_yaw, T_gp, start, free, cost=None):
        """put the held piece with its origin at cell_xy (on the table top) and yaw piece_yaw.
        T_gp: pose of the piece in the gripper frame (from the actual grasp)."""
        c, e, top = self.tables[table]
        Tp = np.eye(4)
        Tp[:3, :3] = np.array([[np.cos(piece_yaw), -np.sin(piece_yaw), 0], [np.sin(piece_yaw), np.cos(piece_yaw), 0], [0, 0, 1]])
        Tp[:3, 3] = [cell_xy[0], cell_xy[1], top + .002]
        Tg = Tp @ np.linalg.inv(T_gp)                   # gripper pose that puts the piece there
        gpos, xd = Tg[:3, 3], Tg[:2, 0]
        off = e + .31
        cands = []
        for side in [np.array([-1, 0]), np.array([1, 0]), np.array([0, 1]), np.array([0, -1])]:
            b = c + side * off
            along = np.array([-side[1], side[0]])
            b = b + along * np.clip((gpos[:2] - c) @ along, -e @ np.abs(along) + .1, e @ np.abs(along) - .1)
            d = np.linalg.norm(gpos[:2] - b)
            # place poses lie in the band next to the table, so they are checked against it too
            if d < PLACE_DIST_MAX and (self.is_free(b, free) or self.is_free(b, self.band)):
                cands.append((d + .3 * np.linalg.norm(b - start[:2]) + 5. * self.costly(b, cost), b))
        cands.sort(key=lambda x: x[0])
        for _, b in cands:
            pts = self.astar(start, b, free, cost)
            if pts is None:
                continue
            # face the table squarely first. Turned towards the cell, a corner of the base
            # (half diagonal .354 m) reached into the table (.31 m away), seen by the collision monitor.
            to_table = c - b
            square = np.arctan2(*(np.round(to_table / np.abs(to_table).max()))[::-1])
            for phi in (square, np.arctan2(gpos[1] - b[1], gpos[0] - b[0])):
                base = np.r_[b, phi]
                pre = self.ik(r, base, gpos + [0, 0, .15], xd)
                if pre is None:
                    continue
                place = self.ik(r, base, gpos, xd, pre)
                if place is None or not self.path_ok(r, base, HOME, pre):
                    continue
                return {"base": base, "path": pts, "pre": pre, "place": place,
                        "piece_pose": (cell_xy[0], cell_xy[1], top + .002, piece_yaw)}
        return None

    # pieces on the floor as obstacles that can be cleared -----------------------------------------
    def costly(self, xy, cost):
        i, j = self.cell(xy)
        return cost is not None and 0 <= i < self.nx and 0 <= j < self.ny and cost[i, j] > 0

    def disc(self, xy, rad):
        return (self.X - xy[0]) ** 2 + (self.Y - xy[1]) ** 2 <= rad ** 2

    def inflate(self, occ, exempt=(), start=None):
        """cells where the base centre would touch a piece. exempt: (xy, radius) discs whose pieces do not count
        (the piece being picked); start: the base is there already, it may drive out of the area around it"""
        occ = occ.copy()
        for xy, rad in exempt:
            occ &= ~self.disc(xy, rad)
        k = int(np.ceil(OCC_INFLATE / self.res))
        u, v = np.mgrid[-k:k + 1, -k:k + 1]
        infl = ndimage.binary_dilation(occ, (u ** 2 + v ** 2) * self.res ** 2 <= OCC_INFLATE ** 2)
        if start is not None:
            infl &= ~self.disc(start, START_FREE)
        return infl

    def samples(self, pts, step=None):
        step = step or self.res / 2
        out = [np.asarray(pts[0], float)]
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
            out += [a + (b - a) * s for s in np.linspace(0, 1, n + 1)[1:]]
        return out

    def blocking(self, pts, occ, infl):
        """the pieces a path drives over, in the order it meets them: list of (occupied cells xy, path sample)"""
        lab, _ = ndimage.label(occ, np.ones((3, 3)))
        out, seen = [], set()
        for p in self.samples(pts):
            if not self.is_free(p, infl):
                continue
            near = self.disc(p, OCC_INFLATE + self.res) & occ
            for k in np.unique(lab[near]):
                if k and k not in seen:
                    seen.add(k)
                    m = lab == k
                    out.append((np.c_[self.X[m], self.Y[m]], p))
        return out

    def plan_aside(self, r, base, T_gp, occ, infl, keep_clear, others, floor_top):
        """a floor spot within reach of the base for the held piece: not on other pieces, away from the path that
        is being cleared (keep_clear: points), and inflating as little new area as possible (next to pieces that
        block anyway). Returns arm key frames and the piece pose, or None."""
        cands = []
        for d in ASIDE_DIST:
            for a in np.linspace(-np.pi, np.pi, 24, endpoint=False):
                c = base[:2] + d * np.array([np.cos(base[2] + a), np.sin(base[2] + a)])
                if not (self.room[0] + .3 < c[0] < self.room[1] - .3 and self.room[2] + .3 < c[1] < self.room[3] - .3):
                    continue
                if any(np.all(np.abs(c - tc) < te + .2) for tc, te, _ in self.tables.values()):
                    continue
                if (self.disc(c, .15) & occ).any():
                    continue                              # do not drop it on another piece
                if min((np.linalg.norm(c - q) for q in keep_clear), default=9.) < OCC_INFLATE + .1:
                    continue                              # it would block the path again
                if any(np.linalg.norm(c - o[:2]) < SAFE_DIST for o in others if o is not None):
                    continue
                new = (self.disc(c, OCC_INFLATE + .12) & ~infl).sum()
                cands.append((new + 2. * abs(a) / np.pi, c))
        cands.sort(key=lambda x: x[0])
        yaws = [base[2] + k * np.pi / 2 for k in range(4)]
        for _, c in cands[:8]:
            plan = self.plan_put(r, base, T_gp, c, yaws, floor_top)
            if plan is not None:
                return plan
        return None

    def plan_put(self, r, base, T_gp, xy, yaws, floor_top):
        """arm key frames that put the held piece down on the floor at xy with one of the yaws, base not moving"""
        for yaw in yaws:
            Tp = np.eye(4)
            Tp[:3, :3] = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
            Tp[:3, 3] = [xy[0], xy[1], floor_top + .002]
            Tg = Tp @ np.linalg.inv(T_gp)                 # gripper pose that puts the piece there
            if Tg[2, 2] < .9:
                continue                                  # the gripper must point down
            pre = self.ik(r, base, Tg[:3, 3] + [0, 0, .15], Tg[:2, 0])
            if pre is None:
                continue
            place = self.ik(r, base, Tg[:3, 3], Tg[:2, 0], pre)
            if place is None or not self.path_ok(r, base, HOME, pre):
                continue
            return {"pre": pre, "place": place, "piece_pose": (xy[0], xy[1], floor_top + .002, wrap(yaw))}
        return None
