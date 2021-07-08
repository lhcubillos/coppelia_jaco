import rospy
import geometry_msgs.msg as gm
import moveit_commander
import moveit_msgs.msg
from math import pi
from collections import defaultdict
import sys
from imu_processing import compute_velocity
import numpy as np
import copy
import time


class Simulation:
    def __init__(self):
        rospy.init_node("jaco_simulation", anonymous=True)
        self.subscribers = [rospy.Subscriber(
            "yei_imu/" + str(i + 1), gm.Vector3, callback=self.imu_callback, callback_args="yei_imu/" + str(i + 1)) for i in range(8)]

        self.imu_data = defaultdict(lambda: [None, None])

        # Gazebo
        joint_state_topic = ['joint_states:=/j2s6s300/joint_states']
        moveit_commander.roscpp_initialize(joint_state_topic)
        moveit_commander.roscpp_initialize(sys.argv)

        self.robot = moveit_commander.RobotCommander()
        self.scene = moveit_commander.PlanningSceneInterface()
        self.group_name = "arm"
        self.move_group = moveit_commander.MoveGroupCommander(self.group_name)
        self.move_group.set_planner_id("RRTConnectConfigDefault")
        print(self.move_group.get_planner_id())
        self.planning_frame = self.move_group.get_planning_frame()
        self.eef_link = self.move_group.get_end_effector_link()

    def imu_callback(self, data, topic):
        pitch = data.y
        roll = data.z
        imu_num = int(topic[-1])
        self.imu_data[imu_num] = [pitch, roll]
        # FIXME: only valid for one IMU
        vel = compute_velocity([[pitch, roll]])

        self.execute_cartesian_path(vel)

    def execute_cartesian_path(self, vel):

        norm = np.linalg.norm(vel)
        if norm < 0.1:
            return

        self.move_group.clear_pose_targets()
        waypoints = []
        wpose = self.move_group.get_current_pose().pose
        # waypoints.append(copy.deepcopy(wpose))
        wpose.position.x = -0.3
        wpose.orientation.x = -0.707
        wpose.orientation.y = 0.0
        wpose.orientation.z = 0.0
        wpose.orientation.w = 0.707

        vel_norm = np.array(vel) / np.linalg.norm(vel)
        scale = 0.1
        wpose.position.y += scale * vel_norm[1]
        wpose.position.z += scale * vel_norm[2]
        waypoints.append(copy.deepcopy(wpose))

        start = time.time()
        plan, fraction = self.move_group.compute_cartesian_path(
            waypoints, 0.01, 7.0)
        end = time.time() - start
        print(end)
        self.move_group.execute(plan, wait=True)
        print(time.time() - start)

    def run(self):
        # First, move robot to initial pose
        initial_pose = self.move_group.get_current_pose().pose
        initial_pose.position.x = -0.3
        initial_pose.orientation.x = -0.707
        initial_pose.orientation.y = 0.0
        initial_pose.orientation.z = 0.0
        initial_pose.orientation.w = 0.707

        start = time.time()
        self.move_group.set_pose_target(initial_pose)
        end1 = time.time() - start
        print(end1)
        self.move_group.go(wait=True)
        end2 = time.time() - start
        print(end2)
        self.move_group.stop()
        self.move_group.clear_pose_targets()
        end3 = time.time() - start
        print(end2)

        time.sleep(5)

        print("Ready to start")
        # Then, start receiving messages and moving the robot accordingly
        rospy.spin()


if __name__ == "__main__":
    sim = Simulation()
    sim.run()
