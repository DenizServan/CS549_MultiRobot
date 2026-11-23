"""
This script serves to setup the full environment by pulling the defined scene and placing the letters and numbers in a random
and difficult manner.

Run it directly to look at a scene:      python place_characters.py
Use it from another script:              from place_characters import build_scene
                                         C, character_frames, floor_z = build_scene(seed=0)
"""

# IMPORTS:
import robotic as ry #type: ignore
import numpy as np

CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
LETTER_HEIGHT = 0.04                                    # thickness of a character


# ---------------- helpers: each one gets everything it needs as an argument ----------------

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


def footprint(C, name):
    """x-y box (lo, hi corners) that an object covers on the floor."""
    f = C.getFrame(name)
    R = f.getRotationMatrix()
    e = np.abs(R) @ (np.array(f.getSize()[:3]) / 2)   # half-extents in world axes
    c = f.getPosition()
    return c[:2] - e[:2], c[:2] + e[:2]                 # lo, hi corners


def outside_boxes(x, y, boxes, r, margin=0.05):
    """True if a letter of radius r at (x, y) stays clear of all boxes."""
    p = np.array([x, y])
    for lo, hi in boxes:
        closest = np.clip(p, lo, hi)                    # nearest point of the box to the letter centre
        if np.linalg.norm(p - closest) < r + margin:
            return False
    return True


def settle(C, frames, seconds=3.0, dt=0.005):
    """Let gravity settle the given frames with PhysX.
    Simulates a copy of the whole scene; the robots are held at their current joint values by position
    control, so only the letters move. Afterwards the resting poses are copied back into C."""
    S = ry.Config()
    S.addConfigurationCopy(C)
    q0 = S.getJointState()
    sim = ry.Simulation(S, ry.SimulationEngine.physx, verbose=0)
    for k in range(int(seconds / dt)):
        sim.step(q0, dt, ry.ControlMode.position)
    for name in frames:
        C.getFrame(name).setPose(S.getFrame(name).getPose())


# ---------------- the one function other scripts call ----------------

def build_scene(seed=0, n_copies=3, r=0.135, do_settle=True):
    """Load the search area, add n_copies of every character and scatter them randomly.

    seed      -> same seed, same layout (use different seeds to test perception on many layouts)
    r         -> radius of the circle around a letter used for spacing (letters are 12 x 24 cm)
    returns   C, character_frames (parent frame names, e.g. 'c0_char_A'), floor_z (floor top height)
    """
    # PULL THE SCENE:
    C = ry.Config()
    C.addFile("graph_files/search_area.g")

    # ADD THE CHARACTERS (all loaded under the floor for now; we place them ourselves):
    for copy in range(n_copies):
        C.addFile("graph_files/characters.g", f"c{copy}_")

    # We move the parent frames to move the characters, so build the list of parent frame names:
    character_frames = [f"c{copy}_char_{ch}" for copy in range(n_copies) for ch in CHARACTERS]

    # floor top: we want to place the letters on the floor, not inside it
    floor = C.getFrame("floor")
    floor_z = floor.getPosition()[2] + floor.getSize()[2]/2

    # free area: inside the walls, shrunk by the letter radius, outside the tables and robot bases
    xmin, xmax, ymin, ymax = find_room_limits(C)
    boxes = [footprint(C, t) for t in ["table_left", "table_right", "mobile_base_1", "mobile_base_2"]]

    rng = np.random.default_rng(seed=seed)
    placed = []                                         # (x, y, top z) of every letter placed so far
    for idx in rng.permutation(len(character_frames)):
        name = character_frames[idx]
        for attempt in range(1000):
            x, y = rng.uniform([xmin + r, ymin + r], [xmax - r, ymax - r])
            if outside_boxes(x, y, boxes, r):
                break
        else:
            raise RuntimeError(f"no free spot for {name}")
        yaw = rng.uniform(-np.pi, np.pi)

        # if its circle overlaps the circle of a letter already placed, start it on top of that letter
        # (it may float a bit above the strokes; the physics lets it drop into place):
        z = floor_z
        for px, py, top in placed:
            if np.hypot(x - px, y - py) < 2 * r:
                z = max(z, top)
        placed.append((x, y, z + LETTER_HEIGHT))

        C.getFrame(name).setPose([x, y, z + 0.001, np.cos(yaw/2), 0, 0, np.sin(yaw/2)])

    if do_settle:
        settle(C, character_frames)

    return C, character_frames, floor_z


# ---------------- only runs when you start this file directly, not on import ----------------
if __name__ == "__main__":
    C, character_frames, floor_z = build_scene(seed=0)
    C.view(True)