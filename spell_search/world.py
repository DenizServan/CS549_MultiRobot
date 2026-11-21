# The shared world. Builds the scene with place_characters.py, adds the cameras, and offers
# small helpers to move bases and arms, attach/detach pieces and render camera images.
#
# Execution is kinematic: KOMO/IK plans the arm, the joint states are set along the plan, and a grasped
# piece is rigidly attached to the gripper. PhysX is used only to let the scattered pieces settle
# (place_characters.py). Pieces have no collision shapes here (the planners do not see them); the collision
# monitor in safety.py checks the real contacts separately.
import os
import runpy
import numpy as np
import robotic as ry
from config import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def yaw_of(R):
    return np.arctan2(R[1, 0], R[0, 0])


class World:
    def __init__(self, seed=SEED, n_copies=N_COPIES, rng=None, sentence="", n_pieces=N_PIECES):
        """n_copies of every character; random extra copies up to n_pieces in total (density); every symbol the
        sentence repeats gets at least as many copies as it needs"""
        symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        copies = {s: max(n_copies, sentence.count(s)) for s in symbols}
        pick = np.random.default_rng(seed + 1000)
        while n_pieces is not None and sum(copies.values()) < n_pieces:
            copies[symbols[pick.integers(len(symbols))]] += 1
        extra = {s: c for s, c in copies.items() if c > n_copies}
        g = runpy.run_path(os.path.join(ROOT, "place_characters.py"),
                           init_globals={"SEED": seed, "N_COPIES": n_copies, "EXTRA": extra}, run_name="scene_builder")
        self.C = C = g["C"]
        self.pieces = list(g["character_frames"])
        self.symbol = {n: n.split("_char_")[1] for n in self.pieces}
        self.floor_top = float(g["floor_z"])
        self.rng = rng if rng is not None else np.random.default_rng(seed)

        # pieces are moved kinematically: no collision shapes needed for them in planning
        for n in self.pieces:
            for ch in C.getFrame(n).getChildren():
                ch.setContact(0)

        # cameras: one mast camera per base (looking down), one wrist camera per gripper
        for r in ROBOTS:
            C.addFrame(f"{r}_mast", BASE[r]).setRelativePosition([0, 0, MAST_H]) \
                .setRelativeQuaternion([0, 1, 0, 0]).setShape(ry.ST.marker, [.1]).setAttributes(MAST)
            C.addFrame(f"{r}_wrist", f"{r}_gripper").setRelativePosition([0, .07, .06]) \
                .setRelativeQuaternion([0, 1, 0, 0]).setShape(ry.ST.marker, [.05]).setAttributes(WRIST)
        self.view_cam = ry.CameraView(C)

        names = C.getJointNames()
        self.base_idx = {r: [names.index(f"{BASE[r]}:{i}") for i in range(3)] for r in ROBOTS}
        self.arm_joints = {r: [f"{r}_panda_joint{i}" for i in range(1, 8)] for r in ROBOTS}
        self.arm_idx = {r: [names.index(j) for j in self.arm_joints[r]] for r in ROBOTS}
        self.holding = {r: None for r in ROBOTS}
        self.t = 0.
        self.viewer = False
        self.caption = ""
        self.steps = 0
        self.frame_hook = None          # called every step (video recording)
        self.monitor = None             # safety.CollisionMonitor (evaluation only)

    # --- joints -------------------------------------------------------------------------------
    def q(self):
        return self.C.getJointState()

    def base_pose(self, r):
        q = self.q()[self.base_idx[r]]
        return np.r_[BASE_ORIGIN[r] + q[:2], q[2]]

    def set_base(self, r, pose):
        q = self.q()
        q[self.base_idx[r]] = np.r_[np.asarray(pose[:2]) - BASE_ORIGIN[r], pose[2]]
        self.C.setJointState(q)

    def arm(self, r):
        return self.q()[self.arm_idx[r]].copy()

    def set_arm(self, r, qa):
        q = self.q()
        q[self.arm_idx[r]] = qa
        self.C.setJointState(q)

    # --- pieces -------------------------------------------------------------------------------
    def piece_pose(self, n):
        """ground truth (evaluation only): position of the piece origin and yaw of its frame"""
        f = self.C.getFrame(n)
        return f.getPosition(), yaw_of(f.getRotationMatrix())

    def attach(self, r, n):
        self.C.attach(f"{r}_gripper", n)
        self.holding[r] = n
        if self.monitor is not None:    # lets the monitor tell the grasped piece from others
            self.monitor.attached.append((self.t, r, n))

    def detach(self, r, z):
        """let go: the piece keeps the x, y and yaw it has in the gripper (so grasp and perception errors
        show up in the result) and comes to rest flat at height z (the support surface)"""
        n = self.holding[r]
        f = self.C.getFrame(n)
        p, yaw = f.getPosition(), yaw_of(f.getRotationMatrix())
        self.C.attach("floor", n)
        f.setPose([p[0], p[1], z, np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)])
        self.holding[r] = None
        return n

    # --- cameras ------------------------------------------------------------------------------
    def render(self, cam):
        """rgb image and world point cloud (N x 3, aligned with rgb.reshape(-1, 3)) of a camera"""
        f = self.C.getFrame(cam)
        self.view_cam.setCamera(f)
        rgb, depth = self.view_cam.computeImageAndDepth(self.C)
        valid = depth > 0
        depth = depth + self.rng.normal(0, DEPTH_NOISE, depth.shape).astype(depth.dtype)
        P = ry.depthImage2PointCloud(depth, self.view_cam.getFxycxy()).reshape(-1, 3)
        P = P @ f.getRotationMatrix().T + f.getPosition()
        return rgb, P, valid.reshape(-1)

    # --- clock ----------------------------------------------------------------------------------
    def tick(self):
        self.t += DT
        self.steps += 1
        if self.viewer and self.steps % VIEW_EVERY == 0:
            self.C.view(False, self.caption)
        if self.frame_hook is not None:
            self.frame_hook(self)
        if self.monitor is not None and MONITOR_EVERY and self.steps % MONITOR_EVERY == 0:
            self.monitor.check()


def grasped_piece(world, r, candidates):
    """Which piece (if any) would the closing fingers hold? The gripper centre must lie inside a stroke
    (with 1 cm tolerance across it) and the closing axis must cross the stroke, not run along it."""
    G = world.C.getFrame(f"{r}_gripper")
    g, gx = G.getPosition(), G.getRotationMatrix()[:, 0]
    best = None
    for n in candidates:
        for ch in world.C.getFrame(n).getChildren():
            if not ch.name[len(n):].startswith("_s") or ch.getShapeType() != ry.ST.ssBox:
                continue
            R, p = ch.getRotationMatrix(), ch.getPosition()
            L, Wd, H = ch.getSize()[:3]
            u = R.T @ (g - p)
            if abs(u[0]) < L / 2 - .012 and abs(u[1]) < Wd / 2 + .01 and abs(u[2]) < H / 2 + .015:
                across = abs(R[:, 1] @ gx)             # 1 = closing axis exactly across the stroke
                if across > .7 and (best is None or abs(u[1]) < best[1]):
                    best = (n, abs(u[1]))
    return None if best is None else best[0]
