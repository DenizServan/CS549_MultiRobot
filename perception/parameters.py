"""
Constants and parameters used across the perception pipeline (scene contents, camera intrinsics, thresholds, ...).
They are grouped in the order of the pipeline steps that use them, so read top to bottom alongside the pipeline.
Every pipeline file imports its numbers from here; no other file contains bare numbers.
Derived values are computed from the values above them, never typed in by hand.
Units: meters, radians (names ending in _DEG are degrees), seconds, pixels (_PX).
"""

# ----------------------------------------------- IMPORTS ------------------------------------------------------------------
import os
import numpy as np

# ============================================ 1. SCENE ====================================================================

# SCENE PATHS:
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # parameters.py lives in perception/
GRAPH_FILES_PATH = os.path.join(REPO_ROOT, "graph_files")                 # graph_files folder path
SCENE_FILE = os.path.join(GRAPH_FILES_PATH, "search_area.g")              # room, tables, and robots path
CHARACTERS_FILE = os.path.join(GRAPH_FILES_PATH, "characters.g")          # the 36 character frames path

if not os.path.isdir(GRAPH_FILES_PATH):
    raise FileNotFoundError(f"graph_files not found at {GRAPH_FILES_PATH}")

# SCENE PARAMETERS:
RANDOM_SEED = 0             # random seed for placing the characters on the floor.
WORD = "ROBOTICS"           # default word to spell (the task scene holds its letters TASK_SPARES more times)
SYMBOLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"    # all 36 symbols, in the fixed order every file uses.
N_SYMBOLS = len(SYMBOLS)                            # derived: 36
PIECE_THICKNESS = 0.04      # (meters) vertical thickness of characters.

# SCENE FRAME NAMES:
CHARACTER_FRAME_PREFIX = "char_"    # fixed prefix parameter to slice later
FLOOR_FRAME_NAME = "floor"
WALL_FRAME_NAMES = ["wall_one", "wall_two", "wall_three", "wall_four"]
TABLE_FRAME_NAMES = ["table_left", "table_right"]
BASE_FRAME_NAMES = ["mobile_base_1", "mobile_base_2"]

# PIECE PLACEMENT PARAMETERS (used only by the scene builder):
LETTER_RADIUS = 0.135               # (meters) to keep distance from walls
TABLE_MARGIN = 0.05                 # (meters) extra clearance between a piece and the tables / bases
HEIGHT_MAP_CELL = 0.01              # (meters) cell size of the height map used to stack overlapping pieces
OUTLINE_SAMPLE_STEP = 0.008         # (meters) spacing of the points that describe a piece's outline when placing it
MAX_PLACEMENT_ATTEMPTS = 1000       # tries to find a free spot for one piece before giving up
PLACEMENT_LIFT = 0.001              # (meters) small gap so a placed piece does not start inside what is under it

# SETTLING PARAMETERS (physics, run once when the scene is built):
SETTLE_DROP_HEIGHT = 0.05           # (meters) pieces start this much above their spot and fall into place
SETTLE_DURATION = 3.0               # (seconds) simulated time the physics runs
SETTLE_TIME_STEP = 0.005            # (seconds) physics step
SETTLE_CHECK_WINDOW = 0.5           # (seconds) the last part of the run used to check that pieces stopped moving
SETTLE_OBSTACLE_NAMES = [FLOOR_FRAME_NAME] + WALL_FRAME_NAMES + TABLE_FRAME_NAMES + BASE_FRAME_NAMES   # derived
STATIC_OBSTACLE_NAMES = [FLOOR_FRAME_NAME] + WALL_FRAME_NAMES + TABLE_FRAME_NAMES       # derived: without the bases

# ---- THE TASK SCENE (scene_builder.buildScene): every symbol once + the word's letters TASK_SPARES more times;
# a share of the pieces dropped in a few piles, the rest scattered over the floor, some of them close to the walls.
TASK_SPARES = 2                    # extra copies of each letter of the word (so each needed letter exists 3 times)
PILE_SHARE = 0.3                   # share of all pieces that are dropped in piles
PILE_ZONES = 3                     # piles in the room
PILE_ZONE_RADIUS = 0.15            # (meters) pieces start within this distance of their pile centre (small: real piles)
PILE_ZONE_GAP = 1.5                # (meters) minimum distance between pile centres
PILE_KEEP_OUT = 0.6                # (meters) scattered pieces keep at least this far from a pile centre
PILE_LAYER_GAP = 0.015             # (meters) vertical gap between pieces dropped on one pile (one piece per layer)
PILE_MAX_TILT_DEG = 20.            # (deg) pieces start tilted up to this, so they lean after settling
PILE_SETTLE_DURATION = 4.0         # (seconds) physics time for the piles to come to rest
WALL_SHARE = 0.25                  # share of the scattered pieces placed close to a wall
WALL_BAND = 0.25                   # (meters) those pieces' centres lie at most this much beyond LETTER_RADIUS from a wall
WALL_NEAR = LETTER_RADIUS + WALL_BAND   # derived: 0.385 m, a piece this close to a wall counts as "near a wall"

# ============================================ 2. CAMERAS ==================================================================
# Depth images are exact: no sensor noise is simulated.

LOOK_DOWN_QUATERNION = [0., 1., 0., 0.]   # (w, x, y, z) 180 deg about x: the camera's z axis points straight down
CAMERA_MARKER_SIZE = 0.1                  # (meters) size of the marker that shows a camera in the viewer

# MAST CAMERA (search, far view):
MAST_WIDTH_PX = 640
MAST_HEIGHT_PX = 480
MAST_FOCAL_FRACTION = 0.5                 # RAI focalLength: focal length as a fraction of the image height
MAST_NEAR = 0.1                           # (meters) closer surfaces are not measured
MAST_FAR = 5.0                            # (meters) farther surfaces are not measured
MAST_OFFSET = [0., 0., 1.6]               # (meters) camera position relative to the base frame
MAST_FOCAL_PX = MAST_FOCAL_FRACTION * MAST_HEIGHT_PX                          # derived: 240 px

# WRIST CAMERA (close-up before grasping):
WRIST_WIDTH_PX = 480
WRIST_HEIGHT_PX = 480
WRIST_FOCAL_FRACTION = 0.7
WRIST_NEAR = 0.05                         # (meters)
WRIST_FAR = 2.0                           # (meters)
WRIST_OFFSET = [0., 0.07, 0.06]           # (meters) camera position relative to the gripper frame
WRIST_VIEW_HEIGHT = 0.45                  # (meters) camera height above a piece's top face for a close-up
WRIST_FOCAL_PX = WRIST_FOCAL_FRACTION * WRIST_HEIGHT_PX                       # derived: 336 px

# ROBOTS AND CAMERA FRAMES:
ROBOT_NAMES = ["p1", "p2"]                              # prefixes of the robot frames in search_area.g
ROBOT_BASE = dict(zip(ROBOT_NAMES, BASE_FRAME_NAMES))   # derived: {"p1": "mobile_base_1", "p2": "mobile_base_2"}
GRIPPER_FRAME_PATTERN = "{robot}_gripper"               # gripper frame of a robot (panda.g), e.g. "p1_gripper"
MAST_CAMERA_PATTERN = "{robot}_mast"                    # name of a robot's mast camera frame
WRIST_CAMERA_PATTERN = "{robot}_wrist"                  # name of a robot's wrist camera frame
TEST_CAMERA_NAME = "test_cam"                           # the free camera, not attached to any robot
TEST_CAMERA_KIND = "mast"                               # intrinsics the test camera copies: "mast" or "wrist"
TEST_CAMERA_HEIGHT = 1.70                               # (meters) default test camera height above the floor
TEST_WRIST_CAMERA_NAME = "test_cam_wrist"               # a second free camera with wrist intrinsics (evaluation, CNN data)

# ============================================ 3. SEGMENTATION =============================================================

SEG_MIN_HEIGHT = 0.012                    # (meters) lower points are floor; well below a piece top (0.04)
SEG_MAX_HEIGHT = 0.25                     # (meters) higher points are robots or tables, not pieces
TABLE_EXCLUDE_MARGIN = 0.03               # (meters) extra band ignored around each table (its edges)
BASE_SIZE = 0.5                           # (meters) side of the square mobile base
BASE_EXCLUDE_MARGIN = 0.17                # (meters) extra band around a base; also removes the robot's own arm
BASE_EXCLUDE_HALF = BASE_SIZE / 2 + BASE_EXCLUDE_MARGIN   # derived: 0.42 m half-size of the ignored square
OTHER_GRIPPER_LOW = 0.40                  # (meters) another robot's gripper lower than this above the floor ...
OTHER_GRIPPER_IGNORE_HALF = 0.25          # (meters) ... is ignored in a square of this half size (it looks like a piece)
SEG_MAX_SLOPE_DEG = 60.                   # (deg) steeper surfaces (piece side walls) are not part of any blob
SEG_DEPTH_JUMP = 0.015                    # (meters) neighbouring pixels further apart in height are different surfaces
                                          # (a piece is 0.04 thick; a tilted piece changes by millimetres per pixel)
SEG_GRID_CELL = 0.01                      # (meters) cell used to measure point density (points per 1 cm cell)
SEG_MIN_POINTS = 25                       # smaller groups are specks
SEG_MAX_EXTENT = 0.60                     # (meters) wider groups are not a piece or a small cluster of pieces
BORDER_MARGIN_PX = 2                      # a blob with a pixel this close to the image edge counts as cut off

# ============================================ 4. BLOB DESCRIPTION =========================================================

PLANE_INLIER_TOLERANCE = 0.01             # (meters) points this close to the fitted plane form the top face
MAX_TILT_DEG = 15                         # a read of a surface tilted more than this is not trusted (conf 0): on the task
                                          # scene CNN reads of pieces tilted 15-35 deg were wrong 5-6 % of the time when
                                          # trusted; such pieces lie on piles and are spread (put down flat) instead
DARK_THRESHOLD = 25                       # (0-255) a top point is a black bottom mark if R, G and B are all below this
STACKED_HEIGHT = 0.065                    # (meters) top higher than this above the floor: lies on another piece
MAX_DARK_SHARE = 0.5                      # a surface with more than this share of black points is a piece's black base
                                          # layer (seen beside a tilted piece, or a piece lying upside down): not read
                                          # (between one piece, 0.04, and two, 0.08)

# ============================================ 5. TEMPLATES ================================================================

TEMPLATE_SAMPLE_STEP = 0.002              # (meters) spacing of model points on the stroke boxes
TEMPLATE_HALF_X = 0.12                    # (meters) half-width of the window around a letter's centroid (strokes reach 0.11)
TEMPLATE_HALF_Y = 0.19                    # (meters) half-height of that window (strokes reach 0.18 from the centroid)
DOT_RADIUS = 0.0067                       # (meters) radius of the black glyph-bottom marks (characters.g)
SYM180_THRESHOLD = 0.85                   # overlap with itself turned 180 deg above this: "looks the same upside down"
SYM180_GRID_CELL = 0.005                  # (meters) grid used for that overlap test

# ============================================ 6. CLASSIFICATION (TEMPLATES) ===============================================

COARSE_GRID_CELL = 0.01                                                    # (meters) grid for the coarse search
COARSE_ANGLE_STEP_DEG = 5                                                  # spacing of candidate rotations
COARSE_ANGLES = np.radians(np.arange(0, 360, COARSE_ANGLE_STEP_DEG))       # derived: 72 angles
N_ANGLES = len(COARSE_ANGLES)                                              # derived: 72
SHIFT_RANGE = 0.03                                                         # (meters) how far a template may slide
SHIFT_CELLS = int(round(SHIFT_RANGE / COARSE_GRID_CELL))                   # derived: 3 cells
VISIBILITY_AWARE = True                   # template strokes under a covering piece count less as missing
UNSEEN_DISCOUNT = 0.5                     # share of such a stroke's penalty that is dropped (1: no penalty at all)
DOT_WEIGHT = 0.25                         # weight of the mark term in the score (+DOT_WEIGHT all on marks, -DOT_WEIGHT none)
DIFFERENT_ANGLE_DEG = 25                  # same symbol turned more than this counts as a different answer
RUNNER_UP_RATIO = 0.85                    # other symbols scoring above this share of the best are kept as alternatives

# ============================================ 7. REFINEMENT ===============================================================

FINE_GRID_CELL = COARSE_GRID_CELL / 2                                      # derived: 0.005 m
FINE_ANGLE_RANGE_DEG = 6                  # search +- this around the coarse angle
FINE_ANGLE_STEP_DEG = 1
FINE_ANGLES = np.radians(np.arange(-FINE_ANGLE_RANGE_DEG, FINE_ANGLE_RANGE_DEG + FINE_ANGLE_STEP_DEG,
                                   FINE_ANGLE_STEP_DEG))                   # derived: 13 angle offsets
FINE_SHIFT_CELLS = 2 * SHIFT_CELLS + 2    # derived: 8 cells of 5 mm
COVERAGE_THRESHOLD = 0.85                 # template explains less than this share of the blob: more than one piece
COVERAGE_FLOOR = 0.60                     # confidence falls to zero at this coverage
EXPLAINED_TOLERANCE = 0.012               # (meters) a point this close to a template stroke is explained by it
MAX_SPLIT_DEPTH = 2                       # how many times a touching blob may be split
MIN_SPLIT_POINTS = 40                     # a split-off part needs at least this many points to be read again

# ============================================ 8. CONFIDENCE AND DECISIONS =================================================
# CONF_ACT / CONF_VERIFY / CONF_ACCEPT: the scale cnn/train.py maps the CNN's margins onto, and the defaults. The values
# the robots act on are READER_THRESHOLDS below (evaluate.py measures them and prints them).

TARGET_ERROR_FAR = 0.03                   # share of trusted far (mast) reads allowed to be wrong
TARGET_ERROR_CLOSE = 0.01                 # share of trusted close (wrist) reads allowed to be wrong
CONF_ACT = 0.10                           # far read worth driving to
CONF_VERIFY = 0.02                        # far read worth a closer look
CONF_ACCEPT = 0.03                        # close read accepted

# (CONF_ACT, CONF_VERIFY, CONF_ACCEPT) the ROBOTS act on, per reader, measured on the task scene with
# evaluate.py --reader <reader> --seeds 80-89 (CALIBRATION_SEEDS). Used by motion/spell.py and robot_run.py.
READER_THRESHOLDS = {"cnn": (0.02, 0.01, 0.02), "template": (0.15, 0.075, 0.15)}

FIT_SPARSE = (0.30, 0.40)                 # fit check of BOTH readers (confidence.fitPenalty): fine-fit score below the low
                                          # end -> conf 0, above the high end -> unchanged; for sparse (far) views
FIT_DENSE = (0.55, 0.70)                  # the same ramp for dense (close-up) views. A fragment of a bigger piece fits a
                                          # simple glyph (L, J, 1) with a big margin but a low score: on the task scene the
                                          # template reader trusted such reads 10-20 % wrong without this check
DENSE_POINTS_PER_CELL = 4.                # points per 1 cm cell above which a view counts as dense

DISTRUST_CUT = True                       # a read of a piece cut by the image border gets confidence 0 (look again)
DISTRUST_OCCLUDED = True                  # a read of a piece partly covered by another one gets confidence 0

# ============================================ 9. EVALUATION ===============================================================
# Ground truth may only be used by ground_truth.py, evaluate.py and cnn/dataset.py.

TUNING_SEEDS = list(range(0, 60))         # scenes for CNN training data (cnn/dataset.py)
CALIBRATION_SEEDS = list(range(80, 90))   # scenes the thresholds are measured on (evaluate.py --seeds 80-89)
TEST_SEEDS = list(range(100, 110))        # scenes never used for tuning or training
FAR_VIEWS_PER_SCENE = 12                  # far camera placements per scene
CLOSE_VIEWS_PER_SCENE = 40                # close camera placements per scene
CLOSE_VIEW_HEIGHTS = (0.32, 0.45)         # (meters) close views: camera this high above the piece top (as the robot's
                                          # wrist looks, motion_parameters.WRIST_LOOKS), drawn uniformly in between
CLOSE_VIEW_OFFSET_STD = 0.05              # (meters) ... and this far off-centre (the robot also looks from the side)
EVAL_WORD_LENGTH = 8                      # evaluation / training scenes use a random word of this many symbols
VIEW_SEED_OFFSET = 10_000                 # view placements use seed + this, so they differ from piece placement
MATCH_DISTANCE = 0.05                     # (meters) a read belongs to a true piece if this close
ANGLE_TOLERANCE_DEG = 10                  # a read's angle counts as right within this (180 deg allowed if symmetric)
LABEL_EXPLAINED_SHARE = 0.9               # a blob gets a label if one true piece explains this share of its points
LABEL_TOLERANCE = 0.008                   # (meters) "explained" distance used for labelling
FLAT_TILT_DEG = 5                         # a true piece tilted less than this counts as flat (evaluation categories)
LABEL_MIN_VISIBLE = 0.6                   # a blob is labelled only if it shows this share of the piece's strokes
LABEL_MAX_TILT_DEG = 30                   # tilted top pieces up to this angle are used as CNN training examples

# ============================================ 10. CNN =====================================================================

CNN_INPUT_LAYERS = 3                      # outline, black marks, hidden region
CNN_IMAGE_SIZE_PX = 64                    # input image side
CNN_RESOLUTION = 0.005                    # (meters) per input pixel
CNN_WINDOW = CNN_IMAGE_SIZE_PX * CNN_RESOLUTION                            # derived: 0.32 m
CNN_N_ANGLE_BINS = N_ANGLES                                                # derived: 72 bins of 5 deg
CNN_YAW_SIGMA_BINS = 1.0                  # width of the soft angle target, in bins
CNN_YAW_NEIGHBOURS = 2                    # bins on each side used for the angle estimate and the angle margin
CNN_KEEP_RANGE = (0.35, 1.0)              # share of points kept in augmentation
CNN_JITTER = 0.002                        # (meters) point jitter in augmentation
CNN_OCCLUDE_SHARE = 0.4                   # share of training samples given a fake covering piece in augmentation
CNN_OCCLUDE_RADIUS = (0.04, 0.10)         # (meters) radius range of that fake covering disc
CNN_SHIFT = 0.008                         # (meters) centre shift in augmentation
CNN_EPOCHS = 25
CNN_BATCH_SIZE = 64
CNN_LEARNING_RATE = 2e-3
CNN_MAX_LEARNING_RATE = 3e-3              # peak of the one-cycle schedule
CNN_WEIGHT_DECAY = 1e-4
CNN_VALIDATION_SHARE = 0.2                # last share of the training scenes held out for validation and calibration
CNN_MIN_RUNNER_UP_PROB = 0.1              # other symbols above this probability are kept as alternatives
CNN_DATA_DIR = os.path.join(REPO_ROOT, "perception", "cnn", "data")
CNN_WEIGHTS_FILE = os.path.join(REPO_ROOT, "perception", "cnn", "cnn_weights.pt")

# ============================================ 11. ROBOT RUN (integration with the team's motion planning) ==============
# Folder of the team repository's spell_search/ (agents.py, planning.py, coordination.py, run.py, ...).
# Default: a CS549_MultiRobot clone next to this repository; override with --team on the command line.
TEAM_SPELL_SEARCH_PATH = os.path.join(os.path.dirname(REPO_ROOT), "CS549_MultiRobot", "spell_search")
# the team's robots use READER_THRESHOLDS (section 8), like motion/

# ============ 12. ROBOT TEST (robot_test.py: one robot, basic motions, to watch perception in the scene) ============
TEST_ROBOT = "p1"                         # the robot that does the test
BASE_ORIGIN_PATTERN = "base_origin_{i}"   # frame the base joints (x, y, yaw) are measured from; i = 1 for p1
ARM_HOME = [0., -.5, 0., -2., 0., 2., -.5]   # (rad) arm joints while driving (the team's HOME)
N_TARGETS = 6                             # pieces the robot goes to
PICK_DISTANCE = 0.65                      # (meters) base centre to grasp point (keeps the piece clear of the base's ignore box)
PICK_TRIES = 12                           # base positions tried around the grasp point if the first one fails
ORIGIN_BELOW_TOP = 0.04                   # (meters) piece origin below its top face (as in the team's code)
GRASP_ABOVE_ORIGIN = 0.02                 # (meters) gripper frame height above the piece origin when grasping
PRE_GRASP_LIFT = 0.15                     # (meters) gripper above the grasp point before going down / after lifting
WRIST_MATCH_DISTANCE = 0.07               # (meters) a wrist read belongs to the target if this close to the mast read
VISITED_DISTANCE = 0.15                   # (meters) reads this close to an already visited piece are skipped
GRASP_TOL_XY = 0.015                      # (meters) the grasp holds if the gripper is this close to the true grasp point
GRASP_TOL_ANGLE_DEG = 15.                 # (deg) ... and its closing axis this close to the true one
IK_TOLERANCE = 0.02                       # KOMO solution rejected above this constraint error
ANIMATION_STEPS = 25                      # interpolation steps per motion shown in the viewer
ANIMATION_STEP_TIME = 0.02                # (s) pause per step
SET_ASIDE_DISTANCE = 0.35                 # (meters) a piece taken off a pile is put down this far from the pile
SET_ASIDE_TRIES = 16                      # directions tried around the pile for the set-aside spot
GRASP_TOL_Z = 0.015                       # (meters) the grasp holds only if the gripper height is this close too
