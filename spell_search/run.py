# Entry point (run from the CS449_Project_ws folder). Two mobile Pandas search the room for the characters of a sentence and
# spell it on their tables (first word on table_left by p1, second word on table_right by p2).
#
#   python run.py                                   live viewer, sentence and seed from config.py
#   python run.py --sentence "CS549 2026" --seed 3
#   python run.py --headless                        no viewer (cameras still need a display: xvfb-run -a on a server)
#   python run.py --no-reread                       ablation: grasp from the mast read, no wrist re-read
#   python run.py --video out                       record an overview camera to out/run.mp4 (4x real time, needs ffmpeg)
#   python run.py --json results.json               write the metrics to a file
#   python run.py --no-monitor                      skip the ground-truth collision monitor (safety.py)
#   python run.py --no-clear                        ablation: the bases drive over pieces instead of clearing the way
#   python run.py --time 300                        stop after 300 s of simulated time (default MAX_TIME)
#   python run.py --cnn                             learned symbol reader (cnn.py, needs cnn_weights.pt) instead of templates
#
# One loop step = DT (50 ms) of simulated time: every robot generator (agents.py) advances one step, the traffic
# rules are updated (coordination.py) and the world ticks (viewer, video, collision monitor). At the end the
# tables are scored against the ground truth (right symbol, right cell, readable) and the metrics are printed.
import os
import sys
import json
import time
import shutil
import subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import *
from world import World, wrap
from perception import Templates
from planning import Planner
from coordination import Blackboard, Traffic
from agents import Robot, table_cells, UPRIGHT


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def viewpoints(planner):
    x0, x1, y0, y1 = planner.room
    xs = np.arange(x0 + VIEWPOINT_STEP / 2, x1, VIEWPOINT_STEP)
    ys = np.arange(y0 + VIEWPOINT_STEP / 2, y1, VIEWPOINT_STEP)
    free = planner.free_grid([])
    return [{"xy": np.array([x, y]), "state": "free", "by": None} for x in xs for y in ys
            if planner.is_free(np.array([x, y]), free)]


def evaluate(W, bb, tpl):
    """sentence accuracy: right symbol, in its cell, readable (upright, or turned by 180 deg for a glyph
    that looks the same that way)"""
    rows, correct = [], 0
    for r in ROBOTS:
        for i, ((want, xy), n) in enumerate(zip(bb.cells[r], bb.cell_piece[r])):
            if n is None:
                rows.append((r, i + 1, want, "-", "empty", False))
                continue
            p, yaw = W.piece_pose(n)
            dyaw = np.degrees(abs(wrap(yaw - UPRIGHT)))
            readable = dyaw < 15 or (tpl.sym180[W.symbol[n]] and abs(dyaw - 180) < 15)
            ok = W.symbol[n] == want and readable and np.linalg.norm(p[:2] - xy) < .05
            correct += ok
            rows.append((r, i + 1, want, W.symbol[n], f"yaw err {dyaw:5.1f} deg, pos err {100 * np.linalg.norm(p[:2] - xy):.1f} cm", ok))
    return correct, rows


def main():
    sentence = arg("--sentence", SENTENCE)
    seed = int(arg("--seed", SEED))
    headless = "--headless" in sys.argv
    reread = "--no-reread" not in sys.argv
    clear = CLEAR and "--no-clear" not in sys.argv
    video = arg("--video", None)
    max_time = float(arg("--time", MAX_TIME))
    use_cnn = "--cnn" in sys.argv
    if use_cnn:                                  # learned symbol reader (cnn.py) instead of template matching
        import perception
        from cnn import Classifier
        perception.CLASSIFIER = Classifier()

    t_wall = time.time()
    W = World(seed=seed, sentence=sentence)
    tpl = Templates(W.C, W.pieces, W.symbol)
    P = Planner(W)
    P.tpl = tpl
    cells = {r: table_cells(W, TABLE[r]) for r in ROBOTS}
    bb = Blackboard(sentence, cells)
    bb.viewpoints = viewpoints(P)
    bb.occ = np.zeros((P.nx, P.ny), bool)                            # shared floor occupancy
    bb.hard = np.zeros((P.nx, P.ny), bool)
    tr = Traffic(W)
    keys = ["think_time", "wait_time", "drive_dist", "mast_reads", "wrist_reads", "rejected", "misreads_caught",
            "grasp_fail", "wrong_piece", "sweeps", "helped",
            "set_aside", "clear_delivered", "clear_fail", "drove_over"]       # clearing the way
    stats = {r: {k: 0 for k in keys} for r in ROBOTS}
    robots = [Robot(r, W, P, tpl, bb, tr, stats[r], reread, clear) for r in ROBOTS]
    W.robots = robots
    print(f"sentence '{sentence}' (seed {seed}, wrist re-read {'on' if reread else 'off'}, "
          f"clearing {'on' if clear else 'off'}, reader {'CNN' if use_cnn else 'templates'}): "
          f"{bb.word['p1']} -> table_left by p1, {bb.word['p2']} -> table_right by p2")

    if video:
        os.makedirs(video, exist_ok=True)
        import robotic as ry
        from PIL import Image
        cam = W.C.addFrame("video_cam").setPosition([-6.6, 0., 9.])
        z = np.array([.6, 0., 0.]) - cam.getPosition()          # look at the middle of the room, +x up in the image
        z /= np.linalg.norm(z)
        x = np.array([0., -1., 0.])
        cam.setRotationMatrix(np.c_[x, np.cross(z, x), z])
        # size and frame rate from config.py; frames are piped straight into ffmpeg instead of
        # being written as PNG files first (PNG encoding cost as much as rendering, ~25 ms per frame)
        cam.setAttributes({"focalLength": .95, "width": VIDEO_SIZE[0], "height": VIDEO_SIZE[1], "zRange": [.1, 20]})
        vcam = ry.CameraView(W.C)
        vcam.setCamera(cam)
        counter = [0]
        fps_out = 4. / (DT * VIDEO_EVERY)            # 4x real time
        enc = None
        if shutil.which("ffmpeg"):
            enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                    "-s", f"{VIDEO_SIZE[0]}x{VIDEO_SIZE[1]}", "-framerate", f"{fps_out:g}", "-i", "-",
                                    "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                                    "-preset", "veryfast", os.path.join(video, "run.mp4")], stdin=subprocess.PIPE)

        def hook(w):
            if w.steps % VIDEO_EVERY == 0:
                img = vcam.computeImageAndDepth(w.C)[0]
                if enc is not None:
                    enc.stdin.write(np.ascontiguousarray(img[..., :3], dtype=np.uint8).tobytes())
                else:                                # no ffmpeg: keep the frames as PNG files
                    Image.fromarray(img).save(os.path.join(video, f"f{counter[0]:05d}.png"))
                counter[0] += 1
        W.frame_hook = hook
    # ground-truth collision monitor (after all frames exist, its copy must match the world)
    monitor = None
    if "--no-monitor" not in sys.argv:
        from safety import CollisionMonitor
        monitor = W.monitor = CollisionMonitor(W)
    if not headless:
        W.viewer = True
        W.C.view(False, "starting")

    agents = [rb.run() for rb in robots]
    while W.t < max_time and not all(bb.done(r) for r in ROBOTS):
        bb.t = W.t
        for a in agents:
            next(a)
        tr.update()
        W.tick()
    reason = "sentence complete" if all(bb.done(r) for r in ROBOTS) else "timeout"

    correct, rows = evaluate(W, bb, tpl)
    n_cells = sum(len(bb.cells[r]) for r in ROBOTS)
    print(f"\n{reason} after {W.t:.1f} s simulated ({time.time() - t_wall:.0f} s wall)")
    print(f"sentence accuracy: {correct}/{n_cells} cells correct and readable")
    for r, i, want, got, info, ok in rows:
        print(f"  {r} cell {i}: '{want}' -> '{got}'  {info}  {'OK' if ok else 'WRONG'}")
    print(f"map: {len(bb.map)} hypotheses, viewpoints done: {sum(v['state'] == 'done' for v in bb.viewpoints)}/{len(bb.viewpoints)}")
    print(f"coordination: min base distance {tr.min_dist:.2f} m (limit {SAFE_DIST}), {tr.stops} stops, "
          f"{tr.lock_waits:.1f} s waiting for the workspace lock")
    # what the ground-truth collision monitor saw
    if monitor is not None:
        coll, depth = monitor.summary()
        print("collisions (contact episodes, deepest penetration): " +
              ", ".join(f"{k} {v} ({1000 * depth[k]:.0f} mm)" for k, v in coll.items()))
    for r in ROBOTS:
        print(f"  {r}: " + ", ".join(f"{k} {v:.1f}" if isinstance(v, float) else f"{k} {v}" for k, v in stats[r].items()))
    if use_cnn:
        c = perception.CLASSIFIER
        print(f"CNN reader: {c.calls} reads, {1000 * c.seconds / max(c.calls, 1):.0f} ms per read")
    result = {"sentence": sentence, "seed": seed, "reread": reread, "clear": clear, "reader": "cnn" if use_cnn else "templates", "reason": reason, "sim_time": round(W.t, 1),
              "correct": correct, "cells": n_cells, "min_base_dist": round(float(tr.min_dist), 3), "stops": tr.stops,
              "lock_wait": round(tr.lock_waits, 1), "stats": stats,
              "events": bb.events}
    if monitor is not None:
        result["collisions"], result["collision_depth"] = monitor.summary()
        result["collision_events"] = monitor.events
    if arg("--json", None):
        with open(arg("--json", None), "w") as f:
            json.dump(result, f, indent=1, default=float)
    if video:
        mp4 = os.path.join(video, "run.mp4")
        # the frames already went into ffmpeg while the run was going
        if enc is not None:
            enc.stdin.close()
            enc.wait()
            print(f"video: {mp4} ({counter[0]} frames, 4x real time)")
        else:
            print(f"video: {counter[0]} PNG frames in {video}/ (ffmpeg not found)")
    if not headless:
        W.C.view(True, f"{reason}: {correct}/{n_cells} correct - press a key to close")
    return result


if __name__ == "__main__":
    main()
