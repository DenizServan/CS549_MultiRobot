# All parameters of the search-and-spell pipeline in one place (imported with `from config import *`).
# Units: metres, radians, seconds. Change a value here, not in the modules.
import numpy as np

# --- task ----------------------------------------------------------------------------------------
SENTENCE = "CS549 2026"      # first word -> table_left (robot 1), second word -> table_right (robot 2)
SEED = 0
MAX_TIME = 1800.             # simulated seconds before the run is stopped (timeout)
N_COPIES = 1                 # copies of every character in the room (a symbol the sentence repeats gets more)
N_PIECES = 72                # total pieces in the room (density): every character N_COPIES times, the rest random
                             # extra copies (seeded); None = exactly N_COPIES of each. 37 = sparse, 108 = very dense

# --- simulation clock ---------------------------------------------------------------------------
DT = .05                     # one agent step = 50 ms of simulated time
VIEW_EVERY = 2               # update the live viewer every N steps

# --- robots ---------------------------------------------------------------------------------------
ROBOTS = ("p1", "p2")
BASE = {"p1": "mobile_base_1", "p2": "mobile_base_2"}
BASE_ORIGIN = {"p1": np.array([.8, 1.]), "p2": np.array([.8, -1.])}   # the transXYPhi joint is relative to these
TABLE = {"p1": "table_left", "p2": "table_right"}
BASE_RADIUS = .36            # half diagonal of the .5 x .5 base
V_BASE, W_BASE = .6, 1.2     # m/s, rad/s
V_JOINT = 1.2                # rad/s, max joint speed of the arm
HOME = np.array([0., -.5, 0., -2., 0., 2., -.5])

# --- reach (measured with IK, see planning.py) -----------------------------------------------------
PICK_DIST = (.52, .58, .64)  # base centre -> piece, tried in this order
PLACE_DIST_MAX = .78

# --- coordination ---------------------------------------------------------------------------
SAFE_DIST = 1.25             # minimum distance between the two base centres (> arm reach + half base)
ARM_LOCK_DIST = 1.9          # closer than this, only one arm may work at a time (workspace lock)
WAIT_STEP = 1.0              # s to wait before re-planning when blocked
WAIT_OTHER = 30.             # s a robot holding a piece waits for the other robot to leave the table it needs

# --- cameras ---------------------------------------------------------------------------------------
MAST_H = 1.6                 # mast camera height above the base centre, looking down
MAST = dict(focalLength=.5, width=640, height=480, zRange=[.1, 5.])
WRIST = dict(focalLength=.7, width=480, height=480, zRange=[.05, 2.])
WRIST_VIEW_H = .45           # gripper height above the piece when re-reading it
DEPTH_NOISE = .002           # m, Gaussian noise on depth images

# --- perception --------------------------------------------------------------------------------
GRID = .01                   # template grid resolution (m)
HOLE_W = .25                 # weight of the bottom marks in the match score (they separate 6/9, N/Z, ...)
ANGLES = np.radians(np.arange(0, 360, 5))
CONF_ACT = .10               # a mast read above this is good enough to go and pick the piece
CONF_VERIFY = .02            # below CONF_ACT: only worth a closer look with the wrist camera
CONF_ACCEPT = .03            # a wrist read below this is rejected (measured: wrong wrist reads have ~0, right ones >= .03)
MERGE_DIST = .08             # detections closer than this are the same piece

# --- search ----------------------------------------------------------------------------------------
VIEWPOINT_STEP = 2.2         # spacing of the search viewpoints (m)

# --- evaluation --------------------------------------------------------------------------
MONITOR_EVERY = 2            # ground-truth collision check every N steps (10 Hz); 0 turns the monitor off
MONITOR_DEPTH = .003         # m, penetrations shallower than this do not count (pieces resting on each other)

# --- video ------------------------------------------------------------------------------
VIDEO_SIZE = (960, 720)      # overview camera resolution
VIDEO_EVERY = 4              # one frame every N steps (= 5 frames per simulated second)

# --- clearing the way ---------------------------------------------------------------------
CLEAR = True                 # pieces on the floor are obstacles; blocking ones are moved aside (--no-clear: drive over them)
BASE_SIZE = .5               # m, side of the square base
CLEARANCE = 1.5              # the base passes only where a square CLEARANCE x its size is free of pieces
                             # (0.5 m base -> 0.75 m corridor); otherwise the way is cleared piece by piece
OCC_INFLATE = CLEARANCE * BASE_SIZE / 2 + .05   # m, base centre to the nearest occupied cell (+ half a grid cell)
START_FREE = OCC_INFLATE + .03   # m, around the start of a path the base may drive out of inflated cells
CELL_COST = 15.              # extra A* cost of entering a cell that touches a piece (grid steps of 10 cm)
OCC_EVERY = 20               # steps between depth-only occupancy updates while driving (1 s)
ASIDE_DIST = (.55, .62, .5)  # m, base centre -> spot where a cleared piece is put down
