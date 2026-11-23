"""
Back-projection: takes a picture with any camera in the scene and turns it into a 3D point cloud in room coordinates.
Also gives the regions (tables, robot bases) that segmentation will filter out.
"""
import numpy as np
import robotic as ry #type: ignore
import parameters as prm
from scene_builder import getHalfExtentsWorld, getFloorTop


def takePicture(view, C, camera_name):
    """
    Renders a camera (view = ry.CameraView(C), made once and reused) and returns (rgb, points, valid, image_size):
    N x 3 colours, N x 3 room points, N valid flags (row i = the same pixel in all three) and (H, W).
    """
    frame = C.getFrame(camera_name)
    view.setCamera(frame)
    rgb, depth = view.computeImageAndDepth(C)                                   # H x W x 3 colours, H x W depths
    points_cam = ry.depthImage2PointCloud(depth, view.getFxycxy())              # H x W x 3 points in the camera frame
    points = points_cam.reshape(-1, 3) @ frame.getRotationMatrix().T + frame.getPosition()   # p_room = R p_cam + t
    return rgb.reshape(-1, 3), points, (depth > 0).reshape(-1), depth.shape    # depth 0 = nothing seen


def getIgnoreBoxes(C, camera_name=None):
    """
    Returns the boxes perception ignores, each (centre xy, half size xy) in room coordinates: every table (enlarged by
    TABLE_EXCLUDE_MARGIN), every mobile base (a square of half size BASE_EXCLUDE_HALF around its current position,
    which also removes the robot's own folded arm), and the gripper of every OTHER robot (not the one camera_name
    belongs to) while it is lower than OTHER_GRIPPER_LOW above the floor: it reaches down to a piece and would look
    like one (square of half size OTHER_GRIPPER_IGNORE_HALF). Computed fresh each time because the robots move.
    """
    boxes = []
    for name in prm.TABLE_FRAME_NAMES:
        frame = C.getFrame(name)
        boxes.append((frame.getPosition()[:2], getHalfExtentsWorld(frame)[:2] + prm.TABLE_EXCLUDE_MARGIN))
    for name in prm.BASE_FRAME_NAMES:
        boxes.append((C.getFrame(name).getPosition()[:2], np.array([prm.BASE_EXCLUDE_HALF, prm.BASE_EXCLUDE_HALF])))
    floor_z = getFloorTop(C)
    for robot in prm.ROBOT_NAMES:
        if camera_name is not None and camera_name.startswith(robot + "_"):
            continue                                        # this robot's own gripper (the wrist camera looks past it)
        gripper = C.getFrame(prm.GRIPPER_FRAME_PATTERN.format(robot=robot)).getPosition()
        if gripper[2] - floor_z < prm.OTHER_GRIPPER_LOW:
            boxes.append((gripper[:2], np.full(2, prm.OTHER_GRIPPER_IGNORE_HALF)))
    return boxes
