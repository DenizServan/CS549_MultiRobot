"""Behaviour of one mobile manipulator (a Franka Panda on a transXYPhi base).

Every robot is a Python generator: one `yield` is one simulation step (DT = 50 ms), so run.py can step both
robots in turn and they act at the same time in one world.

Main loop (Robot.run)
    1. Is a piece I need on the shared map?  -> reserve it -> fetch it:
           drive next to it -> wrist camera re-read -> grasp -> drive to my table -> place it upright
       A wrong or unsure wrist read rejects the piece and corrects the map (a misread caught before grasping).
    2. Otherwise search: claim the nearest free viewpoint (away from the other robot), drive there,
       read everything the mast camera sees and add it to the shared map.
    3. When my word is done, help the other robot: fetch the pieces it still needs and place them on its table.

Clearing the way (CLEAR in config.py, switched off with --no-clear)
    The pieces lying on the floor are obstacles. The mast camera's depth image keeps a shared occupancy grid
    up to date (also while driving). The base only passes where a corridor CLEARANCE times its size (0.75 m
    for the 0.5 m base) is free of pieces. go() first looks for such a path. If there is none, it takes the
    cheapest path over pieces and clears the first piece on it, then plans again (the way is cleared piece by
    piece). Every stop to clear also records the pieces around on the shared map (wrist and mast reads):
        - a piece the robot needs itself goes straight to its table,
        - any other piece is put down within reach, off the path, where it blocks as little as possible;
          it stays on the shared map, so the other robot can still use it.
    A robot that holds a piece cannot clear: it puts its own piece down, clears the way, picks its piece up
    again and goes on (deliver). A piece that cannot be cleared (unreadable, grasp fails twice) is driven
    over as a last resort; every such case is counted as 'drove_over'.

Coordination with the other robot is in coordination.py (shared map, reservations, traffic rules), motion
planning in planning.py, perception in perception.py.
"""
import numpy as np
from config import *
from world import wrap, grasped_piece
from planning import T_of
from perception import read, occupancy

UPRIGHT = -np.pi / 2       # piece yaw that reads upright for someone in front of the tables (looking +x)
MAX_CLEAR_DEPTH = 2        # clearing may start another clearing (a piece in the way to the piece in the way)
MAX_PARK = 4               # times a robot puts its own piece down to clear the way to its table


def table_cells(world, table):
    """cell centres of a table in reading order: far row first, each row from the reader's left (+y)"""
    suf = "L" if table == "table_left" else "R"
    xy = [world.C.getFrame(f"area_{k}_{suf}").getPosition()[:2] for k in range(1, 10)]
    return sorted(xy, key=lambda p: (-round(p[0], 2), -round(p[1], 2)))


class Robot:
    def __init__(self, r, world, planner, tpl, bb, traffic, stats, reread=True, clear=CLEAR):
        """r: robot name ('p1'/'p2'); bb: shared Blackboard; traffic: shared Traffic; stats: this robot's counters;
        reread: wrist camera re-read before grasping; clear: pieces are obstacles that get cleared"""
        self.r, self.W, self.P, self.tpl, self.bb, self.tr = r, world, planner, tpl, bb, traffic
        self.stats, self.reread, self.clear = stats, reread, clear
        self.status = "idle"
        self.side = r              # whose table this robot is filling
        self.depth = 0             # how many clearings are going on (nested)
        self.blocked = None        # (blocking piece, path) when go() returns "blocked"

    def say(self, text):
        """status line shown in the viewer caption"""
        self.status = text
        self.W.caption = "   |   ".join(f"{rb.r}: {rb.status}" for rb in self.W.robots)

    def count(self, k, v=1):
        self.stats[k] = self.stats.get(k, 0) + v

    def exclude(self):
        """boxes the cameras ignore: the tables and both robot bases"""
        boxes = [(c, e + .03) for c, e, _ in self.P.tables.values()]
        return boxes + [(self.W.base_pose(o)[:2], np.array([.42, .42])) for o in ROBOTS]

    # --- primitives (each one advances simulated time) -------------------------------------------------
    def wait(self, seconds):
        for _ in range(max(1, int(seconds / DT))):
            yield

    def think(self, seconds):
        """account for computation time (planning / perception) in simulated time"""
        self.stats["think_time"] += seconds
        yield from self.wait(seconds)

    def move_arm(self, qb):
        """joint-space straight line to qb at V_JOINT"""
        qa = self.W.arm(self.r)
        n = max(1, int(np.abs(qb - qa).max() / V_JOINT / DT))
        for s in np.linspace(0, 1, n + 1)[1:]:
            self.W.set_arm(self.r, (1 - s) * qa + s * qb)
            yield

    def arm_session(self):
        """workspace lock: wait until our arm may work (the other arm is not busy close by)"""
        t = 0.
        while not self.tr.begin_arm(self.r):
            if t == 0.:
                self.bb.log(self.r, "traffic", "waits: the other arm is working close by")
            t += DT
            self.tr.lock_waits += DT
            self.stats["wait_time"] += DT
            yield

    def near(self, who, table):
        """robot who stands at, or is headed to, the table (closer than SAFE_DIST to its edge)"""
        c, e, _ = self.P.tables[table]
        return any(p is not None and np.abs(p[:2] - c).max() < e[0] + SAFE_DIST
                   for p in (self.W.base_pose(who), self.tr.goal[who]))

    def make_way(self):
        """the other robot holds a piece and waits for the table I stand at: drive to a spot away from it"""
        r, o = self.r, self.tr.other(self.r)
        c, e, _ = self.P.tables[self.tr.waiting[o]]
        here = self.W.base_pose(r)
        free, infl = self.grids()
        stand = free if infl is None else free & ~infl
        spots = sorted((v["xy"] for v in self.bb.viewpoints
                        if np.abs(v["xy"] - c).max() > e[0] + SAFE_DIST + .3 and self.P.is_free(v["xy"], stand)),
                       key=lambda p: np.linalg.norm(p - here[:2]))
        for xy in spots[:4]:
            pts = self.P.astar(here, xy, free, self.cost(infl))
            if pts is not None:
                self.say("making way")
                self.bb.log(r, "traffic", f"{o} waits for {self.tr.waiting[o]}: making way")
                yield from self.go({"base": np.r_[xy, here[2]], "path": pts})
                self.tr.goal[r] = None
                return
        yield from self.wait(WAIT_STEP)

    # --- occupancy of the floor --------------------------------------------------------------------
    def sense(self):
        """depth-only occupancy update from the mast camera (cells near the other robot's arm are left alone)"""
        o = self.W.base_pose(self.tr.other(self.r))
        seen, occ = occupancy(self.W, f"{self.r}_mast", self.P, self.exclude(), [(o[:2], .95)])
        self.bb.update_occ(seen, occ)

    def grids(self, targets=()):
        """free grid (room, tables, the other robot) and the cells where the base would touch a piece
        (None when clearing is off). targets: pieces about to be picked, they do not count"""
        free = self.P.free_grid(self.tr.obstacles(self.r))
        if not self.clear:
            return free, None
        start = self.W.base_pose(self.r)[:2]
        return free, self.P.inflate(self.bb.occ, [(t, .17) for t in targets], start)

    def cost(self, infl):
        return None if infl is None else infl * CELL_COST

    def is_hard(self, cells):
        """a piece that could not be cleared before (it is driven over instead of trying again)"""
        ij = np.round((cells - self.P.room[[0, 2]]) / self.P.res).astype(int)
        return bool(self.bb.hard[ij[:, 0], ij[:, 1]].any())

    def blocked_ahead(self, xy, rest, start, targets, known):
        """a piece seen after planning (not in 'known') lies on the next 2 m of the path"""
        infl = self.P.inflate(self.bb.occ, [(t, .17) for t in targets], start) & ~self.P.disc(xy, .3)
        if known is not None:
            infl &= ~known
        return any(not self.P.is_free(p, ~infl) for p in self.P.samples([xy] + rest)[:40])

    # --- driving -------------------------------------------------------------------------------------
    def drive(self, pts, phi_goal, targets=(), known=None):
        """follow way points; the heading turns towards the goal heading on the way. Returns False when the
        other robot blocks the way, or (clearing on) when a new piece shows up on the path ahead"""
        start = self.W.base_pose(self.r)
        total = self.P.path_length(pts)
        done, moved = 0., False
        for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
            L = np.linalg.norm(b - a)
            n = max(1, int(L / V_BASE / DT))
            for s in np.linspace(0, 1, n + 1)[1:]:
                xy = a + (b - a) * s
                # only after the first step, so that every attempt moves the robot and time goes on
                if self.clear and moved and self.W.steps % OCC_EVERY == 0:
                    self.sense()
                    if self.blocked_ahead(xy, list(pts[k + 1:]), pts[0], targets, known):
                        self.bb.log(self.r, "clear", "a piece on the path ahead, planning again")
                        return False
                frac = min(1., (done + L * s) / max(total, 1e-6))
                phi = start[2] + wrap(phi_goal - start[2]) * frac
                waited = 0.
                while not self.tr.may_step(self.r, xy):
                    if waited == 0.:
                        self.tr.stops += 1
                    waited += DT
                    self.stats["wait_time"] += DT
                    # blocked: the lower-priority robot (p2) gives way after 1 s and re-plans around the other,
                    # p1 re-plans only if it stays blocked for 6 s (avoids both robots waiting for each other)
                    if waited > (1. if self.r == ROBOTS[1] else 6.):
                        return False
                    yield
                self.W.set_base(self.r, np.r_[xy, phi])
                self.stats["drive_dist"] += L / n
                moved = True
                yield
            done += L
        # final turn on the spot
        cur = self.W.base_pose(self.r)
        n = max(1, int(abs(wrap(phi_goal - cur[2])) / W_BASE / DT))
        for s in np.linspace(0, 1, n + 1)[1:]:
            self.W.set_base(self.r, np.r_[cur[:2], cur[2] + wrap(phi_goal - cur[2]) * s])
            yield
        return True

    def go(self, plan, targets=(), report_block=False):
        """drive to plan['base']. Returns "ok", "fail", or "blocked": only with report_block, when the robot holds
        a piece and the way has to be cleared first (self.blocked = (blocking piece, path); deliver handles it)"""
        r, goal = self.r, plan["base"]
        self.tr.goal[r] = goal
        if not self.clear:                              # pieces are not obstacles: the planned path, re-planned
            for attempt in range(4):                   # around the other robot when it blocks the way
                if (yield from self.drive(plan["path"], goal[2])):
                    return "ok"
                pts = self.P.astar(self.W.base_pose(r), goal, self.P.free_grid(self.tr.obstacles(r)))
                if pts is None:
                    yield from self.wait(WAIT_STEP)
                    continue
                plan["path"] = pts
                self.bb.log(r, "traffic", "blocked by the other robot, re-planned the path")
            return "fail"
        for attempt in range(12):
            free, infl = self.grids(targets)
            pts = self.P.astar(self.W.base_pose(r), goal, free & ~infl)     # a path that touches no piece
            if pts is None:
                pts = self.P.astar(self.W.base_pose(r), goal, free, self.cost(infl))   # cheapest path over pieces
                if pts is None:
                    if attempt == 0:
                        self.bb.log(r, "traffic", "no way to the goal right now (the other robot), waiting")
                    yield from self.wait(WAIT_STEP)
                    continue
                blockers = self.P.blocking(pts, self.bb.occ, infl)
                clearable = [b for b in blockers if not self.is_hard(b[0])]
                if clearable:
                    if self.W.holding[r] is not None:
                        if report_block:
                            self.blocked = (clearable[0], pts)
                            return "blocked"
                    elif self.depth < MAX_CLEAR_DEPTH and attempt < 10:
                        yield from self.clear_way(clearable[0], pts, targets)
                        self.tr.goal[r] = goal
                        continue
                if blockers:
                    self.count("drove_over", len(blockers))
                    why = "holding a piece" if self.W.holding[r] is not None else \
                        "they could not be cleared" if not clearable else "already clearing"
                    self.bb.log(r, "clear", f"drives over {len(blockers)} piece(s) ({why})")
            if (yield from self.drive(pts, goal[2], targets, infl)):
                return "ok"
        return "fail"

    # --- clearing the way --------------------------------------------------------------------------------
    def clear_way(self, blk, path, targets=()):
        """pick up the piece blk = (its occupied cells, where the path meets it) that blocks path"""
        r = self.r
        cells, at = blk
        near = lambda h: np.min(np.linalg.norm(cells - h["xy"], axis=1)) < .15
        if self.taken_by_other(cells):
            self.bb.log(r, "clear", "the piece in the way is being taken by the other robot, waiting")
            yield from self.wait(WAIT_STEP)
            return
        find = lambda: min((h for h in self.bb.map if h["status"] in ("free", "rejected") and near(h)),
                           key=lambda h: np.min(np.linalg.norm(cells - h["xy"], axis=1)), default=None)
        h = find()
        scanned = h is None
        if h is None:                                   # seen only as occupancy: drive up to it and read it
            self.say("clear: looking at a piece in the way")
            pre = self.truncate(path, at)
            if len(pre) > 1 and np.linalg.norm(pre[-1] - pre[0]) > .05:
                _, infl = self.grids(targets)
                yield from self.drive(pre, np.arctan2(*(pre[-1] - pre[-2])[::-1]), targets, infl)
            yield from self.scan()
            h = find()
        if h is None or h["tries"] >= 2:
            ij = np.round((cells - self.P.room[[0, 2]]) / self.P.res).astype(int)
            self.bb.hard[ij[:, 0], ij[:, 1]] = True
            self.count("clear_fail")
            self.bb.log(r, "clear", f"cannot clear the piece at ({cells[:, 0].mean():.2f}, {cells[:, 1].mean():.2f}), "
                                    f"it will be driven over if there is no other way")
            yield from self.wait(DT)
            return
        h["status"], h["owner"], h["want"], h["tier"] = "reserved", r, None, -1
        self.bb.log(r, "clear", f"'{h['symbol']}' at ({h['xy'][0]:.2f}, {h['xy'][1]:.2f}) blocks the way: clearing it")
        self.depth += 1
        try:
            yield from self.fetch(h, clear_for=path)
        finally:
            self.depth -= 1
        if not scanned and self.W.holding[r] is None:
            yield from self.scan()                      # the robot stands in new ground: record what is around

    def taken_by_other(self, cells):
        """the piece on these cells is reserved or held by the other robot"""
        return any(h["status"] in ("reserved", "picked") and h["owner"] not in (None, self.r)
                   and np.min(np.linalg.norm(cells - h["xy"], axis=1)) < .15 for h in self.bb.map)

    @staticmethod
    def truncate(pts, target):
        """the polyline pts up to the point target on it"""
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a
            t = np.clip((target - a) @ ab / max(ab @ ab, 1e-9), 0, 1)
            if np.linalg.norm(a + t * ab - target) < 1e-3:
                out.append(a + t * ab)
                return out
            out.append(b)
        return out

    def set_aside(self, n, h, keep_clear, verified):
        """put the held piece n (map entry h) down within reach, off the path keep_clear; it stays on the map"""
        r, W, P = self.r, self.W, self.P
        self.say(f"setting '{h['symbol']}' aside")
        base = W.base_pose(r)
        G, Pf = W.C.getFrame(f"{r}_gripper"), W.C.getFrame(n)
        T_gp = np.linalg.inv(T_of(G.getPose())) @ T_of(Pf.getPose())
        _, infl = self.grids()
        o = self.tr.other(r)
        others = [W.base_pose(o), self.tr.goal[o]]
        plan = P.plan_aside(r, base, T_gp, self.bb.occ, infl, P.samples(keep_clear, .2), others, W.floor_top) \
            if len(keep_clear) else None
        if plan is None:                                # no spot off the path: any free spot within reach
            plan = P.plan_aside(r, base, T_gp, self.bb.occ, infl, [], others, W.floor_top)
        if plan is None:                                # back where the map last saw it
            plan = P.plan_put(r, base, T_gp, h["xy"], [h["yaw"] + k * np.pi / 2 for k in range(4)], W.floor_top)
        yield from self.think(.3)
        if plan is None:                                # rare: no IK at all; drop it in front of the base
            self.bb.log(r, "clear", f"no spot within reach for '{h['symbol']}', dropping it")
            p = W.C.getFrame(f"{r}_gripper").getPosition()[:2]
            W.detach(r, W.floor_top)
            h.update({"xy": p, "tries": 2})            # its exact pose is unknown now
            self.bb.release_piece(h)
            self.bb.occ[P.disc(p, .14)] = True
            return
        yield from self.arm_session()
        try:
            yield from self.move_arm(plan["pre"])
            yield from self.move_arm(plan["place"])
            W.detach(r, plan["piece_pose"][2])
            yield from self.move_arm(plan["pre"])
            yield from self.move_arm(HOME)
        finally:
            self.tr.end_arm(r)
        x, y, _, yaw = plan["piece_pose"]
        h.update({"xy": np.array([x, y]), "yaw": yaw, "z_top": W.floor_top + .04, "stacked": False, "tries": 0})
        h["verified"] = h["verified"] or verified
        self.bb.release_piece(h)
        self.bb.occ[P.disc((x, y), .14)] = True
        self.count("set_aside")
        self.bb.log(r, "clear", f"set '{h['symbol']}' aside at ({x:.2f}, {y:.2f}), it stays on the map")

    # --- tasks ----------------------------------------------------------------------------------------
    def explore(self, vp):
        """drive to a search viewpoint and scan; a viewpoint that cannot be reached twice is given up"""
        self.say(f"search: going to viewpoint ({vp['xy'][0]:.1f}, {vp['xy'][1]:.1f})")
        free, infl = self.grids()
        here = self.W.base_pose(self.r)
        stand = free if infl is None else free & ~infl  # where the base may stop (not on a piece)
        goal = vp["xy"]
        if not self.P.is_free(goal, stand):             # viewpoint blocked: any free spot nearby
            near = [goal + d * np.array([np.cos(a), np.sin(a)]) for d in (.5, 1.)
                    for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)]
            near = [p for p in near if self.P.is_free(p, stand)]
            goal = near[0] if near else None
        pts = None if goal is None else self.P.astar(here, goal, free, self.cost(infl))
        ok = False
        if pts is not None:
            ok = (yield from self.go({"base": np.r_[goal, here[2]], "path": pts})) == "ok"
            self.tr.goal[self.r] = None
        if not ok:
            vp["fails"] = vp.get("fails", 0) + 1
            if vp["fails"] >= 2:
                vp["state"] = "done"
                self.bb.log(self.r, "search", f"viewpoint ({vp['xy'][0]:.1f}, {vp['xy'][1]:.1f}) cannot be reached, skipped")
            else:
                vp["state"] = "free"
            yield from self.wait(WAIT_STEP)
            return
        yield from self.scan()
        vp["state"] = "done"

    def scan(self):
        """mast camera: read every piece in view, add the reads to the shared map, update the occupancy"""
        self.say("search: mast camera scan")
        reads = read(self.W, self.tpl, f"{self.r}_mast", self.exclude())
        self.stats["mast_reads"] += len(reads)
        new = self.bb.merge(self.r, reads, "mast")
        if self.clear:
            self.sense()
        need = self.bb.needed(self.side, True)
        hits = [x["symbol"] for x in reads if x["symbol"] in need and x["conf"] >= CONF_ACT]
        self.bb.log(self.r, "search", f"mast scan: {len(reads)} pieces seen, {new} new on the map; useful for me: {hits}")
        yield from self.think(.5)

    def fetch(self, h, clear_for=None):
        """pick the piece of map entry h and deliver it. clear_for: the path h blocks; then the piece goes to
        the table if this robot needs it, otherwise it is set aside"""
        got = yield from self.pick(h, clear_for)
        if got is None:
            return
        n, want, verified = got
        if clear_for is not None and want is None:
            yield from self.set_aside(n, h, clear_for, verified)
            return
        if clear_for is not None:
            self.count("clear_delivered")
        yield from self.deliver(n, want, h)

    def pick(self, h, clear_for=None):
        """drive to the piece, re-read it with the wrist camera, grasp it. Returns (piece, symbol wanted or None,
        read confirmed by the wrist camera) or None if it was rejected or could not be reached / grasped"""
        r, W, P = self.r, self.W, self.P
        want = h["want"]
        self.say(f"fetch '{want or '?'}': planning")
        piece_z = h["z_top"] - .04
        free, infl = self.grids([h["xy"]])
        plan = P.plan_pick(r, h, W.base_pose(r), free, piece_z, self.cost(infl))
        yield from self.think(.3)
        if plan is None:
            h["tries"] += 1
            self.bb.release_piece(h)
            self.bb.log(r, "plan", f"no pick plan for '{want}' at ({h['xy'][0]:.2f}, {h['xy'][1]:.2f})")
            return None
        self.say(f"fetch '{want}': driving")
        if (yield from self.go(plan, [h["xy"]])) != "ok":
            self.tr.goal[r] = None
            self.bb.release_piece(h)
            self.bb.log(r, "traffic", f"could not reach '{want}', trying something else")
            return None
        verified = False
        yield from self.arm_session()
        try:
            # --- wrist re-read (proposal feedback: part of the core system) ---
            if self.reread:
                self.say(f"fetch '{want}': wrist camera re-read")
                yield from self.move_arm(plan["view"])
                reads = read(W, self.tpl, f"{r}_wrist", self.exclude())
                yield from self.think(.5)
                near = [x for x in reads if np.linalg.norm(x["xy"] - h["xy"]) < .07]
                x = max(near, key=lambda x: x["conf"]) if near else None
                self.stats["wrist_reads"] += 1
                self.bb.merge(r, reads, "wrist")        # the close-up corrects the map around the piece too
                sure = x is not None and x["conf"] >= CONF_ACCEPT
                if clear_for is not None:
                    # clearing: whatever it is, it goes; a sure read tells whether this robot needs it
                    want = x["symbol"] if sure and x["symbol"] in self.bb.needed(self.side, True) else None
                    if sure:
                        self.bb.log(r, "reread", f"wrist camera: the piece in the way is '{x['symbol']}' "
                                                 f"(conf {x['conf']:.2f})" + (", I need it" if want else ""))
                else:
                    inspect = want is None              # tier 4: look at a blob that could not be read from far
                    if not (sure and (x["symbol"] == want or (inspect and x["symbol"] in self.bb.needed(self.side, True)))):
                        got = "nothing readable" if x is None else f"'{x['symbol']}' (conf {x['conf']:.2f})"
                        what = "inspection" if inspect else f"the mast read '{want}'"
                        self.bb.log(r, "reread", f"wrist camera: {what} rejected, it sees {got}")
                        self.stats["rejected"] += 1
                        if not inspect:
                            h["alts"].discard(want)
                        if sure:
                            if not inspect and x["symbol"] != want and h["tier"] < 2:
                                self.stats["misreads_caught"] += 1
                            self.bb.release_piece(h)
                        else:
                            h["tries"] += 1
                            self.bb.release_piece(h, "rejected")
                        if inspect:
                            h["tries"] = 2              # inspect a blob only once
                        self.bb.merge(r, reads, "wrist")    # now that h is released, correct this entry too
                        yield from self.move_arm(HOME)
                        return None
                    if inspect:
                        want = x["symbol"]
                        self.bb.log(r, "reread", f"wrist camera: inspection found '{want}' (conf {x['conf']:.2f})")
                if sure:                                # grasp key frames for the refined pose, same base
                    verified = True
                    g = self.regrasp({**h, "symbol": x["symbol"], "xy": x["xy"], "yaw": x["yaw"]}, x["z_top"] - .04)
                    if g is not None:
                        plan = {**plan, **g}
            elif clear_for is not None:                 # no re-read: trust a confident mast read
                want = h["symbol"] if h["conf"] >= CONF_ACT and h["symbol"] in self.bb.needed(self.side, True) else None
            # --- grasp ---
            self.say(f"fetch '{want}': grasping")
            yield from self.move_arm(plan["pre"])
            yield from self.move_arm(plan["grasp"])
            n = grasped_piece(W, r, [p for p in W.pieces if p not in self.placed_all()])
            if n is None:
                self.stats["grasp_fail"] += 1
                self.bb.log(r, "grasp", f"grasp of '{want}' failed (fingers would not close on a stroke)")
                h["tries"] += 1
                self.bb.release_piece(h)
                yield from self.move_arm(plan["pre"])
                yield from self.move_arm(HOME)
                return None
            W.attach(r, n)
            h["status"] = "picked"
            if self.clear:
                self.bb.occ[P.disc(h["xy"], .17)] = False   # its cells are free now
            if want is not None and W.symbol[n] != want:    # ground truth, only counted for the metrics
                self.stats["wrong_piece"] += 1
            yield from self.move_arm(plan["pre"])
            yield from self.move_arm(HOME)
        finally:
            self.tr.end_arm(r)
        self.tr.goal[r] = None
        return n, want, verified

    def regrasp(self, est, piece_z):
        """grasp key frames from the current base for a refined piece pose"""
        P, r = self.P, self.r
        base = self.W.base_pose(r)
        g_rel, g_ang = self.tpl.grasp[est["symbol"]]
        c, s = np.cos(est["yaw"]), np.sin(est["yaw"])
        gxy = est["xy"] + np.array([[c, -s], [s, c]]) @ g_rel
        for sign in (0, np.pi):
            psi = est["yaw"] + g_ang + sign
            xd = [np.cos(psi), np.sin(psi)]
            pre = P.ik(r, base, [gxy[0], gxy[1], piece_z + .17], xd, self.W.arm(r))
            grasp = None if pre is None else P.ik(r, base, [gxy[0], gxy[1], piece_z + .02], xd, pre)
            if grasp is not None:
                return {"pre": pre, "grasp": grasp}
        return None

    def placed_all(self):
        return [p for rr in ROBOTS for p in self.bb.cell_piece[rr] if p is not None]

    def deliver(self, n, want, h):
        """carry the held piece n to its cell on my table and place it upright. If the way to the table is
        blocked by pieces, put n down, clear the way, pick n up again and go on (at most MAX_PARK times).
        If the other robot is at that table, keep n and wait for it (at most WAIT_OTHER)"""
        r, W, P, t = self.r, self.W, self.P, self.side
        i = self.bb.take_cell(t, want)
        parked, attempt, waited = 0, 0, 0.
        while attempt < 3 and i is not None:
            h["for"] = None
            cell_xy = self.bb.cells[t][i][1]
            G, Pf = W.C.getFrame(f"{r}_gripper"), W.C.getFrame(n)
            T_gp = np.linalg.inv(T_of(G.getPose())) @ T_of(Pf.getPose())
            self.say(f"deliver '{want}': planning")
            free, infl = self.grids()
            plan = P.plan_place(r, TABLE[t], cell_xy, UPRIGHT, T_gp, W.base_pose(r), free, self.cost(infl))
            yield from self.think(.3)
            res = None
            if plan is not None:
                self.say(f"deliver '{want}': driving to {TABLE[t]}")
                res = yield from self.go(plan, report_block=parked < MAX_PARK and self.depth < MAX_CLEAR_DEPTH)
            o = self.tr.other(r)
            other_in_way = self.near(o, TABLE[t]) or (res == "blocked" and self.taken_by_other(self.blocked[0][0]))
            if res != "ok" and waited < WAIT_OTHER and other_in_way and not (self.tr.waiting[o] and r == ROBOTS[1]):
                # the other robot is at that table, or takes the piece in the way: wait instead of putting mine down
                if waited == 0.:
                    self.bb.log(r, "traffic", f"{o} is in the way to {TABLE[t]}: holding '{want}' and waiting")
                self.tr.waiting[r] = TABLE[t]
                self.say(f"deliver '{want}': waiting for {o} at {TABLE[t]}")
                yield from self.wait(WAIT_STEP)
                waited += WAIT_STEP
                self.stats["wait_time"] += WAIT_STEP
                continue
            self.tr.waiting[r] = None
            if plan is None:
                attempt += 1
                yield from self.wait(2.)
                continue
            if res == "blocked":
                parked += 1
                blk, path = self.blocked
                self.bb.log(r, "clear", f"the way to {TABLE[t]} is blocked: putting '{want}' down to clear it")
                self.bb.cell_state[t][i] = "open"
                yield from self.set_aside(n, h, path, True)
                h.update({"status": "reserved", "owner": r, "want": want, "for": t})   # keep it for myself
                self.depth += 1
                try:
                    yield from self.clear_way(blk, path)
                finally:
                    self.depth -= 1
                got = yield from self.pick(h)
                if got is None:                          # someone else's now, or lost: back to the main loop
                    return
                n = got[0]
                i = self.bb.take_cell(t, want)
                continue
            if res != "ok":
                attempt += 1
                continue
            yield from self.arm_session()
            try:
                self.say(f"deliver '{want}': placing it upright")
                yield from self.move_arm(plan["pre"])
                yield from self.move_arm(plan["place"])
                W.detach(r, plan["piece_pose"][2])
                yield from self.move_arm(plan["pre"])
                yield from self.move_arm(HOME)
            finally:
                self.tr.end_arm(r)
            self.tr.goal[r] = None
            self.bb.cell_state[t][i] = "done"
            self.bb.cell_piece[t][i] = n
            if t != r:
                self.count("helped")
            self.bb.log(r, "place", f"placed '{W.symbol[n]}' in cell {i + 1} of {TABLE[t]} "
                                    f"({sum(s == 'done' for s in self.bb.cell_state[t])}/{len(self.bb.cell_state[t])})"
                                    + (f", helping {t}" if t != r else ""))
            return
        # could not place it (or the other robot filled that cell first): put it down, it stays on the map
        if i is None:
            self.bb.log(r, "plan", f"no open cell for '{want}' on {TABLE[t]} any more, putting it down")
        else:
            self.bb.log(r, "plan", f"could not place '{want}', putting it down")
            self.bb.cell_state[t][i] = "open"
        yield from self.set_aside(n, h, [], True)

    # --- the main loop ------------------------------------------------------------------------------
    def run(self):
        r = self.r
        o = self.tr.other(r)
        yield from self.scan()
        for side in (r, o):                              # my own word first, then help with the other one
            self.side = side
            while not self.bb.done(side):
                steps = self.W.steps
                explored = not any(v["state"] == "free" for v in self.bb.viewpoints)
                h = self.bb.reserve_piece(r, self.W.base_pose(r), [self.tr.goal[o], self.W.base_pose(o)], self.reread,
                                          explored, side)   # runner-up reads and inspections only once the room is searched
                if h is not None:
                    what = f"'{h['want']}'" if h["want"] else "an unreadable blob for inspection"
                    self.bb.log(r, "task", f"reserved {what} (map: '{h['symbol']}', conf {h['conf']:.2f}) at ({h['xy'][0]:.2f}, {h['xy'][1]:.2f})"
                                           + (f" for {TABLE[side]}" if side != r else ""))
                    yield from self.fetch(h)
                else:
                    other_vp = next((v["xy"] for v in self.bb.viewpoints if v["state"] == "claimed" and v["by"] == o), None)
                    vp = self.bb.claim_viewpoint(r, self.W.base_pose(r), other_vp)
                    if vp is not None:
                        yield from self.explore(vp)
                    elif self.tr.waiting[o] is not None and self.near(r, self.tr.waiting[o]):
                        yield from self.make_way()
                    else:
                        # everything searched and nothing useful known: search again (pieces may have been uncovered)
                        if all(v["state"] == "done" for v in self.bb.viewpoints) and self.bb.needed(side, True):
                            for v in self.bb.viewpoints:
                                v["state"], v["fails"] = "free", 0
                            for hh in self.bb.map:
                                if hh["status"] == "rejected":
                                    hh["status"] = "free"
                            self.bb.log(r, "search", "room searched, symbols still missing: starting a new sweep")
                            self.stats["sweeps"] += 1
                        self.say("waiting")
                        yield from self.wait(WAIT_STEP)
                if self.W.steps == steps:                # never loop without letting time go on
                    yield
            if side == r:
                self.bb.log(r, "task", f"word '{self.bb.word[r]}' complete")
                if not self.bb.done(o):
                    self.bb.log(r, "task", f"helping {o}: placing the rest of '{self.bb.word[o]}' on {TABLE[o]}")
        self.say("done")
        while True:
            yield
