# perception/camera.py

Takes a picture with a camera in the scene and turns it into 3-D points in room coordinates.

## takePicture(view, C, camera_name)

1. frame = the camera's frame in C
2. view.setCamera(frame)                         (view = ry.CameraView(C), made once and reused)
3. rgb, depth = view.computeImageAndDepth(C)     H x W x 3 colours, H x W depths (0 = nothing seen)
4. points_cam = depthImage2PointCloud(depth, fx, fy, cx, cy)   H x W x 3, camera frame
5. points = points_cam (flattened to N x 3) @ R.T + t           R, t = camera rotation and position in the room
6. valid = depth > 0 (flattened)
7. return rgb (N x 3), points (N x 3), valid (N), (H, W)
> Row i of rgb, points and valid is the same pixel i. No noise is added: the depth is exact.
> If the cloud looks mirrored or rotated against the truth, the camera transform (step 5) or the camera quaternion is wrong.

## getIgnoreBoxes(C, camera_name)

1. for each table: (centre xy, half size xy + TABLE_EXCLUDE_MARGIN [0.03])
2. for each robot base: (current centre xy, [0.42, 0.42])   0.25 base half size + 0.17 margin (also covers the arm)
3. for each OTHER robot (not the one camera_name belongs to) whose gripper is lower than OTHER_GRIPPER_LOW [0.4 m]
   above the floor: (gripper xy, [0.25, 0.25])   (it reaches down to a piece and would look like one)
4. return the list
> Recomputed every picture because the bases move. A piece within 0.42 m of a base centre is partly or fully hidden.
