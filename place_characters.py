"""
This script serves to setup the full environment by pulling the defined scene and placing the letters and numbers in a random 
and difficult manner.
"""

# IMPORTS:
import robotic as ry #type: ignore
import numpy as np
import os
# Paths are relative to this file, so the script runs from any folder. A caller can set (spell_search/world.py
# runs this file with runpy.run_path(..., init_globals={...})):
#   SEED      random placement
#   N_COPIES  copies of every character
#   EXTRA     {symbol: copies} for symbols that need more copies than N_COPIES (a sentence with a repeated symbol)
HERE = os.path.dirname(os.path.abspath(__file__))
SEED = globals().get("SEED", 0)
N_COPIES = globals().get("N_COPIES", 3)
EXTRA = globals().get("EXTRA", {})

# PULL THE SCENE:
C = ry.Config()
C.addFile(os.path.join(HERE, "graph_files", "search_area.g"))


# ADD THE CHARACTERS:
# characters.g holds all 36 characters, so a file copy is loaded per copy; characters a copy does not need
# (EXTRA) are deleted again, with their child frames.
characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
template = "char_"
n_copies = max([N_COPIES] + list(EXTRA.values()))
wanted = lambda copy, ch: copy < max(N_COPIES, EXTRA.get(ch, 0))

def delete_character(Cfg, name):
    for ch in Cfg.getFrame(name).getChildren():
        Cfg.delFrame(ch.name)
    Cfg.delFrame(name)

def add_characters(Cfg):
    for copy in range(n_copies):
        Cfg.addFile(os.path.join(HERE, "graph_files", "characters.g"), f"c{copy}_")  # they are all loaded under the floor for now. We will place them ourselves so this is ok.
        for ch in characters:
            if not wanted(copy, ch):
                delete_character(Cfg, f"c{copy}_{template}{ch}")

add_characters(C)

# We will move the parent frames to move the characters, so lets build a list of parent frame names:
character_frames = []
for copy in range(n_copies):
    for idx in range(len(characters)):
        if wanted(copy, characters[idx]):
            character_frames.append(f"c{copy}_" + template + characters[idx])

# Let us move a single letter to our scene just for checking that the configuration loaded correctly:
K = ry.Config()
K.addConfigurationCopy(C)
K.getFrame(character_frames[4]).setPosition([3, 3, 3]) # odd placement since it floats but I can see that it works
#K.view(True) # uncomment this if you want to test yourself.

# Now,we place them randomly:
rng = np.random.default_rng(seed = SEED)
# We also want the region to be bounded by walls:
floor = C.getFrame("floor")
floor_z = floor.getPosition()[2] + floor.getSize()[2]/2  #we want to place the letters on the floor, not inside it
def find_room_limits(C):
    f = C.getFrame("floor")
    fx, fy = f.getPosition()[:2]
    sx, sy = f.getSize()[:2]
    xmin, xmax, ymin, ymax = fx - sx/2, fx + sx/2, fy - sy/2, fy + sy/2   # start from the floor edges, then we will subtact the walls

    for wall in ["wall_one", "wall_two", "wall_three", "wall_four"]:
        w = C.getFrame(wall)
        R = w.getRotationMatrix()
        e = np.abs(R) @ (np.array(w.getSize()[:3]) / 2)   # half-extents in world axes
        c = w.getPosition() # wall position
        if e[0] < e[1]:                     # thin in x -> bounds x
            if c[0] > fx: 
                xmax = min(xmax, c[0] - e[0]) # wall x - wall width or xmax, prior in our case
            else:         
                xmin = max(xmin, c[0] + e[0]) # same but for when the wall x is on the other side
        else:                               # thin in y -> bounds y
            if c[1] > fy: 
                ymax = min(ymax, c[1] - e[1])
            else:         
                ymin = max(ymin, c[1] + e[1])
    return xmin, xmax, ymin, ymax

# Now, we can distribute the characters:
xmin, xmax, ymin, ymax = find_room_limits(C)
# shrink the available area by letter radius:
r = 0.135

# table footprints (x-y boxes) that the letters must stay out of:
def footprint(C, name):
    f = C.getFrame(name)
    R = f.getRotationMatrix()
    e = np.abs(R) @ (np.array(f.getSize()[:3]) / 2)   # half-extents in world axes
    c = f.getPosition()
    return c[:2] - e[:2], c[:2] + e[:2]                 # lo, hi corners

table_boxes = [footprint(C, t) for t in ["table_left", "table_right", "mobile_base_1", "mobile_base_2"]]

def outside_tables(x, y, margin=0.05):
    p = np.array([x, y])
    for lo, hi in table_boxes:
        closest = np.clip(p, lo, hi)                    # nearest point of the table to the letter centre
        if np.linalg.norm(p - closest) < r + margin:
            return False
    return True

# letter outlines: points covering the strokes, in the letter's own frame
def letter_points(C, name, step=0.008):
    pts = []
    for s in C.getFrame(name).getChildren():
        if s.getShapeType() != ry.ST.ssBox:             # only the strokes, not the hole discs / markers
            continue
        L, W = s.getSize()[:2]
        cx, cy = s.getRelativePosition()[:2]
        q = s.getRelativeQuaternion()                   # [w, x, y, z], rotation about z only
        a = 2 * np.arctan2(q[3], q[0])
        for u in np.arange(-L/2, L/2 + 1e-9, step):
            for v in np.arange(-W/2, W/2 + 1e-9, step):
                pts.append([cx + u*np.cos(a) - v*np.sin(a), cy + u*np.sin(a) + v*np.cos(a)])
    return np.array(pts)

letter_height = 0.04                                    # thickness of a character
cell = 0.01                                             # height map resolution (1 cm)
height_map = {}                                         # (i, j) -> top z of whatever lies in that cell

# random letter sample:
order = rng.permutation(len(character_frames))
n_stacked = 0
for idx in order:
    name = character_frames[idx]
    for attempt in range(1000):
        # sample position:
        x, y = rng.uniform([xmin + r, ymin + r], [xmax - r, ymax - r])
        if outside_tables(x, y):
            break
    else:
        raise RuntimeError(f"no free spot for {name}")
    # sample z-rotation:
    yaw = rng.uniform(-np.pi, np.pi)

    # where the letter's strokes would lie on the floor:
    Rz = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
    P = letter_points(C, name) @ Rz.T + [x, y]
    cells = {(int(np.floor(px / cell)), int(np.floor(py / cell))) for px, py in P}

    # if it overlaps letters already placed, it rests on top of the highest one under it:
    z = max([floor_z] + [height_map[c] for c in cells if c in height_map])
    if z > floor_z:
        n_stacked += 1
    for c in cells:
        height_map[c] = z + letter_height

    #place the letter:
    C.getFrame(name).setPose([x, y, z + 0.001, np.cos(yaw/2), 0, 0, np.sin(yaw/2)])

print(f"{n_stacked} of {len(order)} characters are lying on top of others")

# let gravity settle them with a physics engine:
# the simulation runs in a separate, physics-only scene (floor, walls, tables, bases + characters),
# so the robots are never touched. Frames without mass stay fixed, the characters' strokes have mass and fall.
def settle(C, names, drop_height=0.05, seconds=3.0, tau=0.005):
    P = ry.Config()
    for obstacle in ["floor", "wall_one", "wall_two", "wall_three", "wall_four",
                     "table_left", "table_right", "mobile_base_1", "mobile_base_2"]:
        f = C.getFrame(obstacle)
        P.addFrame(obstacle).setShape(f.getShapeType(), f.getSize()).setPose(f.getPose()).setContact(1)
    add_characters(P)
    for name in names:
        pose = C.getFrame(name).getPose()
        pose[2] += drop_height                          # start a little above the final spot -> it drops
        P.getFrame(name).setPose(pose)

    sim = ry.Simulation(P, ry.SimulationEngine.physx, verbose=0)
    steps = int(seconds / tau)
    for k in range(steps):
        sim.step([], tau, ry.ControlMode.none)          # no motor commands: only gravity and contacts
        if k == steps - int(0.5 / tau):
            before = np.array([P.getFrame(n).getPosition() for n in names])
    after = np.array([P.getFrame(n).getPosition() for n in names])
    print(f"settled: max speed over the last 0.5 s = {np.linalg.norm(after - before, axis=1).max() / 0.5:.4f} m/s")

    for name in names:                                  # copy the resting poses back into the real scene
        C.getFrame(name).setPose(P.getFrame(name).getPose())

settle(C, character_frames)
# open the viewer only when this file is run directly, not when another script builds the scene with it
if __name__ == "__main__":
    C.view(True)
