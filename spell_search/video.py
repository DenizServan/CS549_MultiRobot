# Videos of a run: a raw video at a fixed speed and a condensed one that speeds through the routine work and
# slows down where something happens, with a caption that says what is going on and how fast it plays.
#
#   rec = Recorder(world, "vid", "run")       records an overview camera into vid/run.mp4 (4x real time) and
#                                              writes the timeline vid/run.timeline.json next to it
#   rec.caption("Goal 1: CS549 2026")          the caption from now on
#   rec.slow(t0, t1, "p1 placed 'C'")          play simulated time t0..t1 slowly (can lie in the past: the
#                                              condensed video is made at the end, from the raw one)
#   rec.close()                                finishes vid/run.mp4 and makes vid/run_condensed.mp4
#
# multiple_run.py uses the Recorder (--video vid). The condensed video can be made again with other speeds, without
# running the simulation again:
#   python3 spell_search/video.py vid/multiple_run.mp4 --fast 60 --slow 2
#
# A video from run.py (which has no timeline) can be condensed too, with the events from its --json file
# (slow around every placement):
#   python3 spell_search/run.py --headless --video vid --json vid/run.json
#   python3 spell_search/video.py vid/run.mp4 --events vid/run.json
#
# How it works: every VIDEO_EVERY simulation steps one frame of the overview camera is piped into ffmpeg (raw
# video), and its simulated time is stored in the timeline. To condense, every raw frame gets a playing speed
# (fast, or slow inside a slow window); a frame that covers dt simulated seconds lasts dt / speed seconds in the
# condensed video, so at 30 fps it is repeated (slow) or most frames are skipped (fast). The caption is drawn on
# each frame with PIL, and the frames are piped into a second ffmpeg.
import os
import sys
import json
import shutil
import subprocess
import numpy as np

FPS = 30
FAST, SLOW = 60., 2.            # x real time in the condensed video


def ffmpeg_writer(path, size, fps):
    return subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{size[0]}x{size[1]}", "-framerate", f"{fps:g}", "-i", "-",
                             "-pix_fmt", "yuv420p", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                             "-preset", "veryfast", path], stdin=subprocess.PIPE)


class Recorder:
    def __init__(self, world, folder, name="run"):
        from config import VIDEO_SIZE, VIDEO_EVERY, DT
        self.W, self.size, self.every, self.dt = world, VIDEO_SIZE, VIDEO_EVERY, DT
        os.makedirs(folder, exist_ok=True)
        self.path = os.path.join(folder, f"{name}.mp4")
        cam = world.C.addFrame("video_cam").setPosition([-6.6, 0., 9.])
        z = np.array([.6, 0., 0.]) - cam.getPosition()      # look at the middle of the room, +x up in the image
        z /= np.linalg.norm(z)
        x = np.array([0., -1., 0.])
        cam.setRotationMatrix(np.c_[x, np.cross(z, x), z])
        cam.setAttributes({"focalLength": .95, "width": self.size[0], "height": self.size[1], "zRange": [.1, 20]})
        self.refresh()
        self.enc = ffmpeg_writer(self.path, self.size, 4. / (DT * VIDEO_EVERY)) if shutil.which("ffmpeg") else None
        if self.enc is None:
            print("video: ffmpeg not found, no video")
        self.times, self.captions, self.slows = [], [], []
        self.text = ""
        world.frame_hook = self.hook
        world.video_refresh = self.refresh

    def refresh(self):
        """frames were added or deleted in the scene: the camera view has to be made again"""
        import robotic as ry
        self.cam = ry.CameraView(self.W.C)
        self.cam.setCamera(self.W.C.getFrame("video_cam"))

    def hook(self, w):
        if self.enc is None or w.steps % self.every:
            return
        img = self.cam.computeImageAndDepth(w.C)[0]
        self.enc.stdin.write(np.ascontiguousarray(img[..., :3], dtype=np.uint8).tobytes())
        self.times.append(round(w.t, 3))
        self.captions.append(self.text)

    def caption(self, text):
        self.text = text

    def slow(self, t0, t1, text=None):
        self.slows.append((t0, t1, text))

    def close(self, fast=FAST, slow=SLOW):
        if self.enc is None:
            return None
        self.enc.stdin.close()
        self.enc.wait()
        tl = self.path[:-4] + ".timeline.json"
        with open(tl, "w") as f:
            json.dump({"times": self.times, "captions": self.captions, "slows": self.slows,
                       "frame_dt": self.dt * self.every, "size": self.size}, f)
        out = condense(self.path, fast, slow)
        print(f"video: {self.path} (4x real time), {out} (condensed: {fast:g}x, {slow:g}x where something happens)")
        return out


def font(size):
    from PIL import ImageFont
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def timeline_from_events(path, events_json, before=6., after=1.):
    """the timeline of a run.py video: run.py writes one frame every VIDEO_EVERY steps (frame k at simulated time
    (k + 1) * VIDEO_EVERY * DT) and logs its events (time, robot, kind, text) in the --json file"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import VIDEO_EVERY, DT
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height,nb_read_frames", "-of", "csv=p=0", path],
                           capture_output=True, text=True).stdout.strip().split(",")
    w, h, n = int(probe[0]), int(probe[1]), int(probe[2])
    with open(events_json) as f:
        res = json.load(f)
    goal = f"Goal: {res.get('sentence', '')}"
    times = [round((k + 1) * VIDEO_EVERY * DT, 3) for k in range(n)]
    slows = [(t - before, t + after, f"{r}: {text}") for t, r, kind, text in res.get("events", []) if kind == "place"]
    return {"times": times, "captions": [goal] * n, "slows": slows, "frame_dt": VIDEO_EVERY * DT, "size": [w, h]}


def condense(path, fast=FAST, slow=SLOW, tl=None):
    """make <name>_condensed.mp4 from <name>.mp4 and <name>.timeline.json (or the timeline tl)"""
    from PIL import Image, ImageDraw
    if tl is None:
        with open(path[:-4] + ".timeline.json") as f:
            tl = json.load(f)
    w, h = tl["size"]
    w2, h2 = w + w % 2, h + h % 2                           # the raw video was padded to even sizes
    out = path[:-4] + "_condensed.mp4"
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = ffmpeg_writer(out, (w2, h2), FPS)
    fonts = {}

    def fit(d, text):
        """the largest font (up to h/26) at which the caption fits the frame width"""
        size = max(14, h2 // 26)
        while True:
            if size not in fonts:
                fonts[size] = font(size)
            x0, y0, x1, y1 = d.textbbox((0, 0), text, font=fonts[size])
            if x1 - x0 <= w2 - 60 or size <= 10:
                return fonts[size], (x0, y0, x1, y1)
            size -= 1
    acc = 0.
    for k, t in enumerate(tl["times"]):
        raw = dec.stdout.read(w2 * h2 * 3)
        if len(raw) < w2 * h2 * 3:
            break
        hit = next((s for s in tl["slows"] if s[0] <= t <= s[1]), None)
        speed = slow if hit else fast
        acc += tl["frame_dt"] / speed * FPS                 # how many output frames this raw frame is worth
        n = int(acc)
        acc -= n
        if n == 0:
            continue
        text = (hit[2] if hit and hit[2] else tl["captions"][k]) or ""
        text = f"{text}  -  {speed:g}x" if text else f"{speed:g}x"
        img = Image.frombytes("RGB", (w2, h2), raw)
        d = ImageDraw.Draw(img)
        fnt, (x0, y0, x1, y1) = fit(d, text)
        pad = 8
        d.rectangle([12, h2 - (y1 - y0) - 3 * pad - 12, 12 + (x1 - x0) + 2 * pad, h2 - 12], fill=(20, 20, 20))
        d.text((12 + pad - x0, h2 - (y1 - y0) - 2 * pad - 12 - y0), text, font=fnt, fill=(255, 255, 255))
        b = img.tobytes()
        for _ in range(n):
            enc.stdin.write(b)
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    return out


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 2:
        raise SystemExit("python3 spell_search/video.py vid/multiple_run.mp4 [--fast 60] [--slow 2]\n"
                         "python3 spell_search/video.py vid/run.mp4 --events vid/run.json   (a run.py video)")
    f = float(a[a.index("--fast") + 1]) if "--fast" in a else FAST
    s = float(a[a.index("--slow") + 1]) if "--slow" in a else SLOW
    tl = timeline_from_events(a[1], a[a.index("--events") + 1]) if "--events" in a else None
    print(condense(a[1], f, s, tl))
