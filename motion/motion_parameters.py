"""
Every number the motion code uses. Shared scene and perception numbers (camera names, piece thickness, the word, ...)
stay in perception/parameters.py and are imported from there as prm. The confidence thresholds the robots act on are
per reader: prm.READER_THRESHOLDS (measured with perception/evaluate.py on the task scene); spell.py copies the chosen
reader's values into prm.CONF_ACT / CONF_VERIFY / CONF_ACCEPT at the start.
"""
import numpy as np

# ============ 1. TASK ============
ROBOTS = ["p1", "p2"]                     # the two robots, working at the same time
TABLES = {"p1": "table_left", "p2": "table_right"}   # each robot spells its part of the word on its own table
UPRIGHT_YAW = -np.pi / 2                  # (rad) piece yaw that reads upright for someone in front of the tables (looking +x)

# ============ 2. TABLE CELLS ============
CELL_FRAME_PATTERN = "area_{k}_{side}"    # the 3 x 3 coloured squares on each table (search_area.g), k = 1..9
TABLE_SIDE = {"table_left": "L", "table_right": "R"}
SKIP_CENTRE_CELL = True                   # the centre square is out of reach from every side of the table
TABLE_STANDOFF = 0.55                     # (meters) base centre to table edge when placing

# ============ 3. ROBOT ============
BASE_ORIGIN_PATTERN = "base_origin_{i}"   # frame the base joints (x, y, yaw) are measured from; i = 1 for p1
ARM_HOME = [0., -.5, 0., -2., 0., 2., -.5]   # (rad) arm joints while driving
BASE_HALF = 0.45                          # (meters) half size of the base footprint (with a small margin)
OTHER_BASE_HALF = 0.40                    # (meters) half size of the other robot's base (planning obstacle)
PATH_CHECK_STEP = 0.05                    # (meters) spacing of the points checked along a base path
PATH_GRID_CELL = 0.1                      # (meters) grid for A* when the straight line is blocked
IK_TOLERANCE = 0.02                       # KOMO solution rejected above this constraint error
LAST_JOINT_LIMIT = 2.8                    # (rad) the last arm joint stays inside +-this (the Panda's limit is ~2.9)

# ============ 4. KEEPING THE TWO ROBOTS APART (clearance.py) ============
# Each robot is a set of balls (base, arm joints, held piece); a motion step is only taken if every ball of the moving
# robot stays SAFETY_MARGIN away from every ball of the other one. Otherwise the robot waits.
BASE_BALL_RADIUS = 0.36                   # (meters) ball around the 0.5 x 0.5 m base
LINK_BALL_RADIUS = 0.10                   # (meters) balls on the arm joints and between them
HELD_BALL_RADIUS = 0.15                   # (meters) ball around a held piece
SAFETY_MARGIN = 0.05                      # (meters) minimum gap between the two robots' balls
CHECK_DISTANCE = 3.0                      # (meters) bases farther apart than this cannot touch: no check
MAX_WAIT_STEPS = 150                      # a motion blocked this many steps in a row gives up (the action fails)
YIELD_WAIT_STEPS = 20                     # ... for driving robots after the first in ROBOTS: they give way sooner
REPLAN_TRIES = 6                          # driveTo re-plans around the other robot this many times before giving up
CORRIDOR_STEP = 0.25                      # (meters) a lower-priority robot plans around boxes this far apart on the line
                                          # from the higher-priority robot's base to its goal
CLAIM_DISTANCE = 1.5                      # (meters) a robot does not start work within this distance of the other
                                          # robot's work point (piece, viewpoint) or base goal

# ============ 5. MOTION STEPS (kinematic, but in small steps so the clearance can be checked) ============
MAX_JOINT_STEP = 0.05                     # (rad) largest arm joint change per step
MAX_BASE_STEP = 0.05                      # (meters) largest base move per step
MAX_TURN_STEP = 0.10                      # (rad) largest base turn per step
STEP_TIME = 0.01                          # (s) pause per step in the viewer (both robots move in one step)
MAX_STEPS = 60000                         # the whole run stops after this many steps

# ============ 6. SEARCH ============
MAP_MERGE_DISTANCE = 0.05                 # (meters) a new read this close to a map entry belongs to that entry
FORGET_FRACTION = 0.8                     # an entry inside this share of a camera's view (inscribed disc) that the new
                                          # picture does not read again is forgotten (the piece moved or was taken)
EXPLORE_SPACING = 1.5                     # (meters) spacing of the grid of viewpoints the robots scan from
MAX_TRIES_PER_PIECE = 2                   # a map entry is given up after this many failed picks / looks
MAX_ACTIONS = 120                         # actions per robot before it stops
MAX_WAIT_ACTIONS = 40                     # times a robot may wait for the other one (50 steps each) before giving up

# ============ 7. PICK ============
PICK_DISTANCE = 0.65                      # (meters) base centre to grasp point
PICK_TRIES = 12                           # base spots tried around the grasp point
WRIST_MATCH_DISTANCE = 0.07               # (meters) a wrist read belongs to the target if this close to the map entry
ORIGIN_BELOW_TOP = 0.04                   # (meters) piece origin below its top face
GRASP_ABOVE_ORIGIN = 0.02                 # (meters) gripper frame height above the piece origin when grasping
PRE_GRASP_LIFT = 0.15                     # (meters) gripper above the grasp point before going down / after lifting
GRASP_TOL_XY = 0.015                      # (meters) the fingers hold the piece if they close this close to the true grasp point,
GRASP_TOL_ANGLE_DEG = 15.                 # (deg) with the closing axis this close to the true one,
GRASP_TOL_Z = 0.015                       # (meters) at this height error at most

# ============ 8. PLACE ============
PLACE_CLEARANCE = 0.005                   # (meters) the piece is let go this far above the table top
PLACE_TRIES = 10                          # if no table side can be used now (the other robot is there), the robot holds
PLACE_WAIT_STEPS = 50                     # the piece, waits this many steps and tries again, this many times

# ============ 9. SPREADING PILES ============
SET_ASIDE_REACHES = (0.75, 0.65)          # (meters) set-aside spots are tried this far from the base (the farther ring
                                          # first; 0.65 = PICK_DISTANCE, where the arm surely reaches the floor)
SET_ASIDE_TRIES = 16                      # directions tried around the base
SET_ASIDE_CLEARANCE = 0.02                # (meters) a set-aside piece is let go this far above the floor (it may be held tilted)
SET_ASIDE_MIN_GAP = 0.30                  # (meters) a set-aside spot keeps at least this far from every piece on the map
SPREAD_PIECE_RADIUS = 0.15                # (meters) reads / map entries this close to where a piece's grasp point was put
                                          # down are that piece (its origin can be ~0.12 m from the grasp point)

# ============ 10. GEOMETRIC GRASP (no symbol needed: a straight piece of stroke, fingers across it) ============
GEO_CANDIDATE_STEP = 0.01                 # (meters) spacing of the candidate grasp points on the piece's top
GEO_NEIGHBOUR_RADIUS = 0.03               # (meters) points this close to a candidate describe its stroke
GEO_MIN_NEIGHBOURS = 30                   # fewer points: no grasp there
GEO_MIN_ELONGATION = 2.                   # stroke straight there if its spread along / across is above this
GEO_MAX_STROKE_WIDTH = 0.04               # (meters) wider across: not a single stroke (a corner or two strokes)
FINGER_WIDTH = 0.02                       # (meters) size of a finger along the stroke
FINGER_GAP = 0.005                        # (meters) free space between the stroke and a finger
FINGER_DEPTH = 0.02                       # (meters) thickness of a finger across the stroke
FINGER_CLEARANCE = 0.01                   # (meters) a point in a finger's place lower than (grasp height - this) is no obstacle
STROKE_HALF_WIDTH = 0.01125               # (meters) half the stroke width of the pieces (characters.g: 0.0225)
GEO_TOL_STROKE = 0.004                    # (meters) truth check: the grasp point lies on a stroke within this
GEO_TOL_ANGLE_DEG = 20.                   # (deg) truth check: closing axis at most this far from across the stroke

# ============ 11. WRIST LOOKS ============
WRIST_LOOKS = [(0.45, 0.0), (0.32, 0.0), (0.45, 0.10)]   # (camera height above the piece top, sideways shift) tried in
                                                         # order until a confident read: far, closer, from the side
                                                         # (perception's CLOSE_VIEW_HEIGHTS match these heights)

# ============ 12. SCORE ============
CELL_MATCH_DISTANCE = 0.12                # (meters) a piece belongs to a cell if its centre is this close
YAW_OK_DEG = 10.                          # (deg) a placed piece counts as upright within this
POSITION_OK = 0.04                        # (meters) ... and as in its cell within this
