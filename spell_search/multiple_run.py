# Several goals in a row (our contribution: multi-word / multi-goal runs), with videos. It uses the task code as it
# is (world.py, coordination.py, agents.py, run.py): this file only builds the run, changes the goal between rounds
# and adds the effects. Run from the CS449_Project_ws folder:
#
#   python3 spell_search/multiple_run.py --cnn                      3 goals: CS549 2026 first, then words from WORDS
#   python3 spell_search/multiple_run.py --cnn --rounds 5
#   python3 spell_search/multiple_run.py --cnn --sentences "RAI ARM,CS549 2026"   (then words from WORDS)
#   python3 spell_search/multiple_run.py --cnn --random             later goals: random strings of the pieces left
#   python3 spell_search/multiple_run.py --cnn --headless --video vid
#           vid/multiple_run.mp4 (4x real time) and vid/multiple_run_condensed.mp4 (60x, 2x where something happens)
#   python3 spell_search/multiple_run.py --time 900                 simulated seconds per goal (default MAX_TIME)
#   python3 spell_search/multiple_run.py --on-timeout stop          end the run when a goal is not reached (default: next)
#   python3 spell_search/multiple_run.py --rounds 1 --video vid     one goal, with the condensed video
#   also as in run.py: --seed, --headless, --no-reread, --no-clear
#
# 1. The goal is written on the wall behind the tables, stroke by stroke.
# 2. The robots spell it on their tables (agents.py, unchanged), with the pieces that lie in the room.
# 3. Goal reached: the spelled pieces burst into confetti and vanish, the wall is painted over, the next goal is
#    written. Goal not reached (timeout): the goal is struck through and the spelled pieces are taken off the
#    tables without confetti; then the next goal (or, with --on-timeout stop, the end).
#    No pieces are added: a goal is only chosen if the pieces left in the room hold its symbols (a --sentences
#    goal that cannot be spelled any more is skipped).
#
# Between goals the Blackboard gets the new words (new_goal below); what the robots know about the pieces still on
# the floor stays on the map. The wall behind the tables (wall_one) is raised to 2 m here, so the text can be large.
# The effects are kinematic frames without contacts, above the 25 cm the cameras look at, so the robots do not see
# them. The collision monitor (safety.py) is not used here, because it keeps a copy of the scene and the scene
# changes between goals.
import os
import sys
import time
import numpy as np
from collections import Counter
import robotic as ry
from scipy.spatial.transform import Rotation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from world import World
from perception import Templates
from planning import Planner
from coordination import Blackboard, Traffic
from agents import Robot, table_cells
from run import arg, viewpoints, evaluate

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR_FILE = os.path.join(os.path.dirname(HERE), "graph_files", "characters.g")
SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# goal words: at most 9 symbols (a table has 3 x 3 cells), only the 36 symbols there are pieces of
WORDS = ["ROBOT", "PANDA", "KOMO", "RAI", "CS449", "CS549", "2026", "BILKENT", "GRASP", "SEARCH", "SPELL", "ARM",
         "LEARN", "CNN", "TEAM", "ANKARA", "AMR", "PHYSX", "KITTING", "LGP", "HELLO", "WORLD", "MOBILE", "PICK", "PLACE"]
WALL_H = 2.                  # m, wall_one is raised to this height for the text
PALETTE = [(1., .1, .55), (.1, .9, 1.), (.6, 1., .1), (1., .55, 0.), (.65, .3, 1.), (1., .95, .1)]
STAT_KEYS = ["think_time", "wait_time", "drive_dist", "mast_reads", "wrist_reads", "rejected", "misreads_caught",
             "grasp_fail", "wrong_piece", "sweeps", "helped",
             "set_aside", "clear_delivered", "clear_fail", "drove_over"]       # as in run.py


def glyph_strokes():
    """stroke boxes of every symbol from characters.g: list of (u, v, length, width, angle) in the glyph plane
    (u to the right, v up, metres; angle of the stroke's length axis)"""
    G = ry.Config()
    G.addFile(CHAR_FILE)
    out = {}
    for s in SYMBOLS:
        f = G.getFrame(f"char_{s}")
        strokes = []
        for ch in f.getChildren():
            if ch.name.startswith(f"char_{s}_s") and ch.getShapeType() == ry.ST.ssBox:
                rel, q = ch.getRelativePosition(), ch.getRelativeQuaternion()
                L, Wd = ch.getSize()[:2]
                strokes.append((rel[0], rel[1], L, Wd, 2 * np.arctan2(q[3], q[0])))
        out[s] = strokes
    return out


class Show:
    """the effects: the goal written on the wall, confetti when it is reached, the wall painted over"""

    def __init__(self, W, strokes, rng):
        self.W, self.C, self.strokes, self.rng = W, W.C, strokes, rng
        self.n = 0                    # frame counter (unique names)
        self.wall = []                # frames of the text on the wall

    def frame(self, shape, size, color, pos):
        self.n += 1
        f = self.C.addFrame(f"fx_{self.n}").setShape(shape, size).setColor(list(color)).setPosition(list(pos))
        f.setContact(0)
        return f

    def ticks(self, n, caption=None):
        if caption:
            self.W.caption = caption
        for _ in range(n):
            t0 = time.time()
            self.W.tick()
            if self.W.viewer:                           # the effects run in real time in the live viewer
                time.sleep(max(0., DT - (time.time() - t0)))

    def refresh(self):
        """frames were added / deleted: cameras and viewer must see the new structure"""
        self.W.view_cam = ry.CameraView(self.C)
        if self.W.viewer:
            self.C.view_recopyMeshes()
        if getattr(self.W, "video_refresh", None):
            self.W.video_refresh()

    # --- the spelled pieces leave the tables -------------------------------------------------------------------
    def clear_tables(self, pieces, confetti=True, keep=False):
        """the pieces shrink away; with confetti (goal reached) they burst into big coloured drops. keep: the pieces
        stay (confetti only, after the last goal)"""
        parts = []
        if confetti:
            for n in pieces:
                p = self.C.getFrame(n).getPosition()
                for _ in range(16):
                    col = PALETTE[self.rng.integers(len(PALETTE))]
                    v = np.r_[self.rng.normal(0, .9, 2), self.rng.uniform(1.5, 3.)]
                    f = self.frame(ry.ST.sphere, [self.rng.uniform(.03, .05)], col, p + [0, 0, .06])
                    parts.append([f, p + [0, 0, .06], v])
            self.refresh()
        shrink = {n: [(ch, np.array(ch.getSize())) for ch in self.C.getFrame(n).getChildren()
                      if ch.getShapeType() == ry.ST.ssBox] for n in pieces}
        steps = 45 if confetti else 20
        for k in range(steps):
            s = 1. - (k + 1) / 15                       # the pieces shrink for 14 steps, then they are gone
            for n in ([] if keep else pieces):
                for ch, size in shrink[n]:
                    if s >= .1:
                        ch.setShape(ry.ST.ssBox, list(np.r_[size[:3] * s, min(size[3], size[:3].min() * s * .4)]))
                    elif k == 14:                       # hide it (deleted below)
                        ch.setShape(ry.ST.ssBox, [1e-3, 1e-3, 1e-3, 1e-4])
            for q in parts:                             # the confetti flies and falls
                q[2][2] -= 9.81 * DT
                q[1] = q[1] + q[2] * DT
                q[1][2] = max(q[1][2], self.W.floor_top + .03)
                q[0].setPosition(list(q[1]))
            self.ticks(1)
        for n in ([] if keep else pieces):              # delete the pieces (children first)
            for ch in self.C.getFrame(n).getChildren():
                self.C.delFrame(ch.name)
            self.C.delFrame(n)
            self.W.pieces.remove(n)
        for q in parts:
            self.C.delFrame(q[0].name)
        self.refresh()

    # --- the wall ------------------------------------------------------------------------------------------------
    @staticmethod
    def raise_wall(W, height=WALL_H):
        """wall_one (behind the tables) becomes `height` tall, same footprint"""
        w = W.C.getFrame("wall_one")
        p = w.getRelativePosition()
        w.setShape(ry.ST.box, [.25, 10., height]).setColor([.8, .8, .8]).setContact(1)
        w.setRelativePosition([p[0], p[1], height / 2])

    def wall_x(self):
        wall = self.C.getFrame("wall_one")              # x = 4.87, inner face at x = 4.745, faces the room (-x)
        return wall.getPosition()[0] - wall.getSize()[0] / 2

    def write(self, sentence):
        """write the goal on wall_one, behind the tables, readable from the room (looking +x), stroke by stroke"""
        xw = self.wall_x()
        n_chars = len(sentence)
        S = min(3.6, 9. / (.17 * n_chars))              # glyph scale: a glyph is 0.24 m tall, 0.86 m at 3.6
        z0 = self.W.floor_top + .35 + .14 * S           # glyph centre: the bottom stays above the cameras' 25 cm
        y = .17 * S * (n_chars - 1) / 2                 # the reader faces +x: their right is -y
        for i, ch in enumerate(sentence):
            if ch == " ":
                y -= .17 * S
                continue
            col = np.array(PALETTE[(i + 1) % len(PALETTE)])
            for (u, v, L, Wd, a) in self.strokes[ch]:
                e1 = np.array([0., -np.cos(a), np.sin(a)])        # along the stroke
                e2 = np.array([0., np.sin(a), np.cos(a)])         # across, in the wall plane
                x, y_, z, w = Rotation.from_matrix(np.c_[e1, e2, np.cross(e1, e2)]).as_quat()
                q = [w, x, y_, z]                               # (setRotationMatrix gave NaN for some angles)
                c = np.array([xw, y - S * u, z0 + S * v])
                Wd = Wd * 1.4                                   # bolder than the pieces
                outline = self.frame(ry.ST.box, [S * L + .03, S * Wd + .03, .004], (.05, .05, .05), c + [-.004, 0, 0])
                outline.setQuaternion(q)
                fill = self.frame(ry.ST.box, [.001, S * Wd, .004], col, c + [-.008, 0, 0])
                fill.setQuaternion(q)
                self.wall += [outline, fill]
                self.refresh()
                for k in range(1, 7):                   # the stroke grows like a pen line
                    fill.setShape(ry.ST.box, [S * L * k / 6, S * Wd, .004]).setColor(list(col))   # setShape resets the colour
                    self.ticks(1)
            y -= .17 * S
        self.ticks(30)

    def strike(self):
        """goal not reached: a red line through the text on the wall"""
        if not self.wall:
            return
        xw = self.wall_x()
        ys = [f.getPosition()[1] for f in self.wall]
        zs = [f.getPosition()[2] for f in self.wall]
        y_hi, y_lo, zc = max(ys) + .2, min(ys) - .2, (max(zs) + min(zs)) / 2
        bar = self.frame(ry.ST.box, [.004, .01, .12], (.85, .05, .05), [xw - .014, y_hi, zc])
        self.wall.append(bar)
        self.refresh()
        n = 20
        for k in range(1, n + 1):
            wd = (y_hi - y_lo) * k / n
            bar.setShape(ry.ST.box, [.004, wd, .12]).setColor([.85, .05, .05]).setPosition([xw - .014, y_hi - wd / 2, zc])
            self.ticks(1)
        self.ticks(30)

    def buff(self):
        """paint the last goal over: a wall-coloured band rolls over it from left to right, then it is gone"""
        if not self.wall:
            return
        xw = self.wall_x()
        ys = [f.getPosition()[1] for f in self.wall]
        zs = [f.getPosition()[2] for f in self.wall]
        y_hi, y_lo = max(ys) + .5, min(ys) - .5
        zc, h = (max(zs) + min(zs)) / 2, max(zs) - min(zs) + .5
        roller = self.frame(ry.ST.box, [.004, .01, h], (.8, .8, .8), [xw - .02, y_hi, zc])
        self.refresh()
        n = 30
        for k in range(1, n + 1):
            wd = (y_hi - y_lo) * k / n
            roller.setShape(ry.ST.box, [.004, wd, h]).setColor([.8, .8, .8]).setPosition([xw - .02, y_hi - wd / 2, zc])
            self.ticks(1)
        for f in self.wall:
            self.C.delFrame(f.name)
        self.C.delFrame(roller.name)
        self.wall = []
        self.refresh()


def available(W):
    """symbols of the pieces still in the room (ground truth: which goals can still be spelled)"""
    return Counter(W.symbol[n] for n in W.pieces)


def feasible(sentence, avail):
    words = sentence.split()
    return len(words) == 2 and all(1 <= len(w) <= 9 for w in words) and not (Counter(sentence.replace(" ", "")) - avail)


def choose_goal(rng, given, k, avail):
    """the next goal: the next --sentences entry that the pieces left can spell; when the list is used up, a pair of
    WORDS (or, with --random / when no pair fits, two random strings of the pieces left). None if not even that
    is possible."""
    for j in range(k, len(given)):
        if feasible(given[j], avail):
            return given[j], j + 1
        print(f"goal '{given[j]}' skipped: the pieces left in the room cannot spell it")
    k = max(k, len(given))
    if "--random" not in sys.argv:
        pairs = [(a, b) for a in WORDS for b in WORDS if a != b]
        for i in rng.permutation(len(pairs)):
            s = " ".join(pairs[i])
            if feasible(s, avail):
                return s, k + 1
    pool = [s for s, c in avail.items() for _ in range(c)]
    if len(pool) < 2:
        return None, k
    pick = list(rng.permutation(pool)[:min(len(pool), int(rng.integers(4, 9)))])
    cut = int(rng.integers(1, len(pick)))
    return "".join(pick[:cut]) + " " + "".join(pick[cut:]), k + 1


def new_goal(bb, tr, robots, cells, sentence):
    """the Blackboard (coordination.py) for the next sentence on the same tables. The pieces spelled before are gone
    (their map entries too); what is known about the pieces still on the floor stays on the map; the search starts
    again (all viewpoints free)."""
    words = sentence.split()
    assert len(words) == 2, "the sentence needs two words, one per table"
    bb.word = dict(zip(ROBOTS, words))
    bb.cells = {r: [(s, cells[r][i]) for i, s in enumerate(bb.word[r])] for r in ROBOTS}
    bb.cell_state = {r: ["open"] * len(bb.word[r]) for r in ROBOTS}
    bb.cell_piece = {r: [None] * len(bb.word[r]) for r in ROBOTS}
    bb.map = [h for h in bb.map if h["status"] != "picked"]       # picked = placed on a table (or held: none now)
    for i, h in enumerate(bb.map):
        h.update({"id": i, "status": "free", "owner": None, "for": None, "tries": 0})
    for v in bb.viewpoints:
        v["state"], v["by"], v["fails"] = "free", None, 0
    bb.hard[:] = False
    for r in ROBOTS:
        tr.goal[r], tr.busy[r], tr.waiting[r] = None, False, None
    for rb in robots:
        rb.side, rb.depth, rb.blocked = rb.r, 0, None


def main():
    seed = int(arg("--seed", SEED))
    rounds = int(arg("--rounds", 3))
    given = [s.strip() for s in arg("--sentences", "").split(",") if s.strip()]
    on_timeout = arg("--on-timeout", "next")
    headless = "--headless" in sys.argv
    reread = "--no-reread" not in sys.argv
    clear = CLEAR and "--no-clear" not in sys.argv
    max_time = float(arg("--time", MAX_TIME))
    video = arg("--video", None)
    use_cnn = "--cnn" in sys.argv
    if use_cnn:                                  # learned symbol reader (cnn.py), as in run.py
        import perception
        from cnn import Classifier
        perception.CLASSIFIER = Classifier()

    # --- the run, built as in run.py ------------------------------------------------------------------------------
    t_wall = time.time()
    sentence = given[0] if given else SENTENCE
    W = World(seed=seed, sentence=sentence)
    Show.raise_wall(W)                                   # before the planner and the cameras copy the scene
    tpl = Templates(W.C, W.pieces, W.symbol)
    P = Planner(W)
    P.tpl = tpl
    cells = {r: table_cells(W, TABLE[r]) for r in ROBOTS}
    bb = Blackboard(sentence, cells)
    bb.viewpoints = viewpoints(P)
    bb.occ = np.zeros((P.nx, P.ny), bool)
    bb.hard = np.zeros((P.nx, P.ny), bool)
    tr = Traffic(W)
    stats = {r: {k: 0 for k in STAT_KEYS} for r in ROBOTS}
    robots = [Robot(r, W, P, tpl, bb, tr, stats[r], reread, clear) for r in ROBOTS]
    W.robots = robots
    rng = np.random.default_rng(seed + 7)
    show = Show(W, glyph_strokes(), rng)
    rec = None
    if video:
        from video import Recorder
        rec = Recorder(W, video, "multiple_run")
    if not headless:
        W.viewer = True
        W.C.view(False, "starting")
    print(f"seed {seed}, reader {'CNN' if use_cnn else 'templates'}, wrist re-read {'on' if reread else 'off'}, "
          f"clearing {'on' if clear else 'off'}, {rounds} goals, on timeout: {on_timeout}")

    slow_from = [None]

    def phase(text, slow):
        """a caption; slow: the condensed video plays this part slowly (effects), else fast (robots at work)"""
        W.caption = text
        if rec is not None:
            rec.caption(text)
        if slow:
            slow_from[0] = W.t

    def end_slow():
        if rec is not None and slow_from[0] is not None:
            rec.slow(slow_from[0], W.t)
        slow_from[0] = None

    def step(agents):
        bb.t = W.t
        for a in agents:
            next(a)
        tr.update()
        W.tick()

    summary, k_given = [], 1
    phase(f"Goal 1 written on the wall: {sentence}", True)
    show.ticks(5)
    show.write(sentence)
    end_slow()
    for k in range(rounds):
        print(f"\n=== goal {k + 1}: '{sentence}' ({bb.word['p1']} -> table_left by p1, {bb.word['p2']} -> table_right "
              f"by p2), {len(W.pieces)} pieces in the room")
        phase(f"Goal {k + 1}: {sentence} - robots searching and spelling", False)
        t0 = W.t
        agents = [rb.run() for rb in robots]
        while W.t - t0 < max_time and not all(bb.done(r) for r in ROBOTS):
            step(agents)
        complete = all(bb.done(r) for r in ROBOTS)
        # let a robot finish what it holds (e.g. a piece it is setting aside), then end the behaviours
        t1 = W.t
        while (any(W.holding[r] is not None for r in ROBOTS) or any(tr.busy.values())) and W.t - t1 < 60:
            step(agents)
        for a in agents:
            a.close()
        for r in ROBOTS:
            if W.holding[r] is not None:                 # rare: put it down where it is
                W.detach(r, W.floor_top)
        correct, rows = evaluate(W, bb, tpl)
        n_cells = sum(len(bb.cells[r]) for r in ROBOTS)
        summary.append((sentence, complete, correct, n_cells, W.t - t0))
        print(f"goal {k + 1}: {'reached' if complete else 'NOT reached (timeout)'} after {W.t - t0:.1f} s, "
              f"{correct}/{n_cells} correct")
        for r, i, want, got, info, ok in rows:
            print(f"  {r} cell {i}: '{want}' -> '{got}'  {info}  {'OK' if ok else 'WRONG'}")
        last = k == rounds - 1 or (not complete and on_timeout == "stop")
        placed = [n for r in ROBOTS for n in bb.cell_piece[r] if n is not None]
        if complete:
            phase(f"Goal {k + 1} reached: {sentence}", True)
            show.ticks(15)
            show.clear_tables(placed, confetti=True, keep=last)
        else:
            phase(f"Goal {k + 1} NOT reached (timeout, {correct}/{n_cells}): {sentence}", True)
            show.strike()
            if not last:
                show.clear_tables(placed, confetti=False)
        end_slow()
        if last:
            break
        nxt, k_given = choose_goal(rng, given, k_given, available(W))
        if nxt is None:
            print("no further goal can be spelled with the pieces left in the room")
            break
        sentence = nxt
        phase(f"Goal {k + 2} written on the wall: {sentence}", True)
        show.buff()
        show.write(sentence)
        end_slow()
        new_goal(bb, tr, robots, cells, sentence)

    print(f"\n{len(summary)} goals, {W.t:.0f} s simulated, {time.time() - t_wall:.0f} s wall")
    for i, (s, ok, c, n, t) in enumerate(summary):
        print(f"  goal {i + 1}: '{s}'  {'reached' if ok else 'not reached'}  {c}/{n} correct  {t:.0f} s")
    for r in ROBOTS:
        print(f"  {r}: " + ", ".join(f"{k} {v:.1f}" if isinstance(v, float) else f"{k} {v}" for k, v in stats[r].items()))
    if rec is not None:
        for t, r, kind, text in bb.events:               # condensed video: slow around every placement
            if kind == "place":
                rec.slow(t - 6., t + 1., f"{r}: {text}")
        rec.close()
    if not headless:
        W.C.view(True, "all goals done - press a key to close")


if __name__ == "__main__":
    main()
