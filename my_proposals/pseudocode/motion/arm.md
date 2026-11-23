# motion/arm.py

Joints and stepwise arm motions. Motions are GENERATORS: each next() takes one small step, so other code uses them
as `yield from moveArm(...)`. spell.py alternates one step of p1 and one of p2.

## getJointIndices(C, robot)
1. base = indices of "<base>:0..2" (x, y, yaw) ; arm = indices of "<robot>_panda_joint1..7"

## moveJoints(C, idx, target, step_sizes, max_wait [MAX_WAIT_STEPS 150])     generator
1. start = current values of the joints idx
2. n = number of steps so that no joint changes more than step_sizes per step (at least 1)
3. s = 1 ; waited = 0
4. while s <= n:
   1. q = FRESH full joint state (the other robot moved in between) ; gap_before = getMinGap(C)
   2. q[idx] = start + (target - start) x s / n ; set it
   3. gap = getMinGap(C)
   4. if gap >= SAFETY_MARGIN [0.05] or gap > gap_before: keep the step ; s += 1 ; waited = 0
   5. else: undo the step (set the old values back) ; waited += 1 ;
      if max_wait is not None and waited > max_wait: raise Blocked
   6. yield                                                   (hand over to the other robot)
> Only the joints idx are written: the other robot's joints are never overwritten.

## moveArm(C, robot, q, max_wait)       generator: moveJoints(arm joints, q, MAX_JOINT_STEP [0.05 rad])
## goHome(C, robot)                     generator: moveArm(ARM_HOME, max_wait = None: waits as long as needed)

## getArmIK(C, robot, position, closing_dir, q_start)
1. copy of C, arm set to q_start, only the 7 arm joints free
2. KOMO 1 slice: joint limits ; gripper position ; gripper z up-axis (0,0,1) ; gripper x = closing_dir
3. solve ; error > IK_TOLERANCE [0.02] -> None ; else the 7 joints
> No collision check here: the clearance is checked step by step while moving.

## runToEnd(C, generator, show)
1. next() until StopIteration ; draw each step if show ; return the generator's result   (debugging one action)
