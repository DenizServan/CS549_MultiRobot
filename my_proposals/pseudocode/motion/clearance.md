# motion/clearance.py

Keeps the two robots apart. Every motion step (arm.moveJoints) asks getMinGap before and after the step.

## getBalls(C, robot)
1. ball (base position, BASE_BALL_RADIUS [0.36])
2. points = positions of <robot>_panda_joint1..7 and the gripper
3. for each pair of neighbouring points: ball on the first (LINK_BALL_RADIUS [0.10]) and one half-way
4. ball on the gripper
5. for each child of the gripper that is a piece (attached = held): ball HELD_BALL_RADIUS [0.15]
6. return the balls

## getGap(C, a, b)
1. all ball pairs (one of a, one of b): centre distance - radius a - radius b
2. return the smallest (negative = overlapping)

## getMinGap(C)
1. for every pair of robots whose bases are closer than CHECK_DISTANCE [3 m]: getGap
2. return the smallest, or inf

## Claims (where a robot is about to work)
- CLAIMS = {robot: {"work": xy, "base": xy}}
- claim(robot, work_xy, base_xy): set ; claim(robot) clears (idle)
- getOtherClaims(C, robot): for every OTHER robot that claims something: its base now, its base goal, its work point
  > an idle robot claims nothing: it is only an obstacle for driving (base.getObstacles)
- isFarFromOthers(C, robot, xy, distance [CLAIM_DISTANCE 1.5 m]): xy at least that far from all those points
