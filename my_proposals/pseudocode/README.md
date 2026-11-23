# Pseudocode, one file per script

Each file walks through its script step by step, one numbered step per semi-major operation, in the order the code
runs. Function names are the real ones (search for them); constants are written NAME [value].
Lines starting with `>` are notes on what to watch when debugging; they are not in the code.

Order of the pipeline:

    perception/scene_builder.py   build the scene
    perception/camera.py          picture -> 3-D points
    perception/segmentation.py    points -> blobs (one per visible surface)
    perception/blob.py            blob -> flat outline + dark dots + hidden region
    perception/templates.py       the 36 letter models
    perception/classify_template.py  or  perception/cnn/classify_cnn.py   blob -> symbol, coarse angle, margin
    perception/refine.py          exact angle + piece origin
    perception/confidence.py      penalties and calibration
    perception/reader.py          runs all of the above per picture, splits touching pieces
    perception/ground_truth.py, evaluate.py, cnn/dataset.py, cnn/train.py, cnn/model.py   evaluation and training
    perception/robot_test.py, robot_run.py                                               perception in a robot
    motion/clearance.py, arm.py, base.py, table.py, piece_map.py                         building blocks
    motion/pick.py, geo_grasp.py, spread.py, place.py, score.py                          actions (generators)
    motion/spell.py                                                                      both robots, step by step

parameters.py and motion_parameters.py only hold constants and are not repeated here.
