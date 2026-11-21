# Cooperation of the two mobile manipulators (Mehmet Can's part of the proposal:
# shared-zone scheduling, piece reservation, collision checks), adapted to robots that search the room.
#
#   Blackboard  - the shared map of piece hypotheses (who saw what, where, how sure), the search
#                 viewpoints, the target cells; every piece and viewpoint is reserved by one robot
#                 at a time, so the robots never go for the same piece or search the same area
#   Traffic     - base motion: the other robot's pose and reserved goal are obstacles for the path
#                 planner; while driving, a robot stops if the other one comes closer than SAFE_DIST;
#                 the workspace lock lets only one arm work while the bases are closer than ARM_LOCK_DIST
#   The Blackboard also holds the shared occupancy grid of the floor (pieces as obstacles, see agents.py,
#   'clearing the way'): occ = cells holding a piece as last seen, hard = pieces that could not be cleared.
import numpy as np
from config import *


class Blackboard:
    def __init__(self, sentence, cells):
        words = sentence.split()
        assert len(words) == 2, "the sentence needs two words, one per table"
        self.word = dict(zip(ROBOTS, words))
        # target cells: (symbol, cell centre xy), in reading order
        self.cells = {r: [(s, cells[r][i]) for i, s in enumerate(self.word[r])] for r in ROBOTS}
        self.cell_state = {r: ["open"] * len(self.word[r]) for r in ROBOTS}
        self.cell_piece = {r: [None] * len(self.word[r]) for r in ROBOTS}
        self.map = []                       # piece hypotheses
        self.viewpoints = []                # {"xy", "state": free / claimed / done, "by"}
        self.events = []                    # (time, robot, kind, text)
        self.t = 0.
        # shared occupancy of the floor (pieces as obstacles), on the planner grid; set in run.py
        self.occ = None                     # cells holding a piece, as last seen
        self.hard = None                    # cells of pieces that could not be cleared (driven around, never over)

    def update_occ(self, seen, occ):
        """what a camera sees replaces what the map held for those cells"""
        self.occ[seen] = occ[seen]

    def log(self, r, kind, text):
        self.events.append((round(self.t, 1), r, kind, text))
        print(f"[{self.t:6.1f}s] {r}: {text}")

    # --- target cells ----------------------------------------------------------------------------
    def needed(self, r, unclaimed=False):
        """symbols still needed on robot r's table (open cells, each counted once); unclaimed: minus the ones
        a robot is already fetching for that table"""
        need = [s for (s, _), st in zip(self.cells[r], self.cell_state[r]) if st == "open"]
        if unclaimed:
            for h in self.map:
                if h["status"] in ("reserved", "picked") and h.get("for") == r and h["want"] in need:
                    need.remove(h["want"])
        return need

    def take_cell(self, r, symbol):
        for i, ((s, xy), st) in enumerate(zip(self.cells[r], self.cell_state[r])):
            if s == symbol and st == "open":
                self.cell_state[r][i] = "assigned"
                return i
        return None

    def done(self, r):
        return all(st == "done" for st in self.cell_state[r])

    # --- the shared map ------------------------------------------------------------------------------
    def merge(self, r, reads, source):
        """add reads to the map. A read close to a known hypothesis updates it (the more confident read wins);
        a hypothesis confirmed by the wrist camera ('verified') is not changed by mast reads any more."""
        new = 0
        keys = ("symbol", "yaw", "xy", "conf", "z_top", "stacked", "prec")
        for x in reads:
            if any(h["status"] in ("reserved", "picked") and np.linalg.norm(h["xy"] - x["xy"]) < MERGE_DIST for h in self.map):
                continue
            h = min((h for h in self.map if h["status"] in ("free", "rejected")),
                    key=lambda h: np.linalg.norm(h["xy"] - x["xy"]), default=None)
            wrist = source == "wrist" and x["conf"] >= CONF_ACCEPT
            if h is not None and np.linalg.norm(h["xy"] - x["xy"]) < MERGE_DIST:
                if wrist or (not h["verified"] and x["conf"] > h["conf"]):
                    h.update({k: x[k] for k in keys})
                    h["seen_by"].add(r)
                    if wrist:
                        h.update({"verified": True, "alts": set(), "status": "free", "tries": 0})
                if not h["verified"]:
                    h["alts"] |= set(x.get("alts", []))
                continue
            self.map.append({**{k: x[k] for k in keys}, "id": len(self.map), "status": "free", "owner": None,
                             "seen_by": {r}, "source": source, "tries": 0, "verified": wrist,
                             "alts": set() if wrist else set(x.get("alts", []))})
            new += 1
        return new

    def reserve_piece(self, r, pos, other=(), verify=True, explored=True, side=None):
        """choose the next piece for robot r and reserve it (for the table of side, default r's own). In this order:
           1. a confident read of a symbol r needs (conf >= CONF_ACT, or confirmed by a wrist camera)
           2. (active detection, needs the wrist re-read) an unsure read of a needed symbol
           3. once the room has been searched: a piece where a needed symbol was the runner-up
           4. once the room has been searched: any blob that could not be read well (touching pieces, ...)
        other: poses of the other robot (current, reserved goal) - pieces in its working area are skipped"""
        side = side or r
        need = set(self.needed(side, True))
        pool = [h for h in self.map if h["status"] == "free" and not h["stacked"] and h["tries"] < 2]
        for o in other:                         # do not walk into the other robot's working area
            if o is not None:
                pool = [h for h in pool if np.linalg.norm(h["xy"] - o[:2]) > SAFE_DIST + .3]
        tiers = [[h for h in pool if h["symbol"] in need and (h["conf"] >= CONF_ACT or h["verified"])]]
        if verify:
            tiers.append([h for h in pool if h["symbol"] in need and h["conf"] >= CONF_VERIFY])
            if explored:
                tiers.append([h for h in pool if h["alts"] & need])
                tiers.append([h for h in pool if not h["verified"] and (h["prec"] < .85 or h["conf"] < CONF_VERIFY)])
        for tier, cands in enumerate(tiers):
            if cands:
                break
        else:
            return None
        h = min(cands, key=lambda h: np.linalg.norm(h["xy"] - pos[:2]) - .5 * h["conf"])
        h["status"], h["owner"], h["for"] = "reserved", r, side
        h["want"] = h["symbol"] if h["symbol"] in need else (sorted(h["alts"] & need)[0] if tier == 2 else None)
        h["tier"] = tier
        return h

    def release_piece(self, h, status="free"):
        h["status"], h["owner"] = status, None

    # --- search -------------------------------------------------------------------------------------
    def claim_viewpoint(self, r, pos, other_claim=None):
        """nearest free viewpoint, keeping away from the one the other robot has claimed"""
        free = [v for v in self.viewpoints if v["state"] == "free"]
        if not free:
            return None

        def cost(v):
            c = np.linalg.norm(v["xy"] - pos[:2])
            if other_claim is not None:
                c += 2. * max(0., 3. - np.linalg.norm(v["xy"] - other_claim))   # spread the two robots out
            return c
        v = min(free, key=cost)
        v["state"], v["by"] = "claimed", r
        return v


class Traffic:
    """base-motion and workspace coordination between the two robots"""

    def __init__(self, world):
        self.W = world
        self.goal = {r: None for r in ROBOTS}           # reserved goal pose of every robot
        self.busy = {r: False for r in ROBOTS}         # arm in a manipulation sequence
        self.waiting = {r: None for r in ROBOTS}       # table a robot holding a piece waits to reach
        self.min_dist = np.inf
        self.stops = 0
        self.lock_waits = 0.

    def other(self, r):
        return ROBOTS[1 - ROBOTS.index(r)]

    def obstacles(self, r):
        o = self.other(r)
        obs = [(self.W.base_pose(o)[:2], SAFE_DIST)]
        if self.goal[o] is not None and self.waiting[o] is None:
            obs.append((self.goal[o][:2], SAFE_DIST))
        return obs

    def dist(self):
        return np.linalg.norm(self.W.base_pose(ROBOTS[0])[:2] - self.W.base_pose(ROBOTS[1])[:2])

    def update(self):
        self.min_dist = min(self.min_dist, self.dist())

    def may_step(self, r, nxt):
        """a driving robot may take its next step if it does not get closer than SAFE_DIST to the other"""
        o = self.W.base_pose(self.other(r))[:2]
        now = np.linalg.norm(self.W.base_pose(r)[:2] - o)
        after = np.linalg.norm(np.asarray(nxt[:2]) - o)
        return after >= SAFE_DIST or after > now      # moving away is always allowed

    def begin_arm(self, r):
        """workspace lock: an arm may start a manipulation unless the other arm is busy close by"""
        if self.busy[self.other(r)] and self.dist() < ARM_LOCK_DIST:
            return False
        self.busy[r] = True
        return True

    def end_arm(self, r):
        self.busy[r] = False
