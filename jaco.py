from pyrep import PyRep
from pyrep.backend import sim, utils
from pyrep.robots.arms.jaco import Jaco
from pyrep.robots.end_effectors.jaco_gripper import JacoGripper
import numpy as np
import time
import threading
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity

# import lcm
# from lcmtypes.imus_t import imus_t
# from lcmtypes.euler_t import euler_t
from zerocm import ZCM
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t


class JacoArm:
    def __init__(self, arm, gripper):
        self.arm = arm
        # self.gripper = gripper


class Simulation:
    def __init__(self, scene_name="scene_jaco.ttt"):
        self.pr = PyRep()
        self.jaco = None

        self.scene_name = scene_name
        self.curr_vel = [0.0, 0.0, 0.0]
        self.new_vel = [0.0, 0.0, 0.0]
        self.should_stop = False
        self.zcmL = ZCM()
        self.imu_data = None

    def imu_t_callback(self, channel, imu_msg):
        self.imu_data = np.array([
            imu_msg.imu_values[0].pitch,imu_msg.imu_values[0].roll,\
            imu_msg.imu_values[1].pitch,imu_msg.imu_values[1].roll,\
            imu_msg.imu_values[2].pitch,imu_msg.imu_values[2].roll,\
            imu_msg.imu_values[3].pitch,imu_msg.imu_values[3].roll
        ]).reshape(1,-1)

    def start(self):
        # ZCM
        self.zcmL.subscribe("IMU", imus_t, self.imu_t_callback)
        self.zcmL.start()
        # IMU stream

        # pygame.init()
        # Launch CS
        self.pr.launch(self.scene_name)
        # Start simulation
        self.pr.start()

        # Get arm from simulation
        self.jaco = JacoArm(Jaco(), None)

    def stop(self):
        self.pr.stop()
        # self.pr.shutdown()

    def run(self):
        try:
            self.start()
            start = time.time()
            while time.time() - start < 3:
                self.pr.step()
            while not self.should_stop:
                try:
                    # print(self.imu_data)
                    # TODO: requires all four imus for now
                    if self.imu_data is not None:
                        self.new_vel = compute_velocity(self.imu_data)
                    if (
                        np.linalg.norm(np.array(self.curr_vel) - np.array(self.new_vel))
                        > 0.001
                    ):
                        self.curr_vel = self.new_vel
                        sim.simSetFloatSignal("vel_x", self.curr_vel[0])
                        sim.simSetFloatSignal("vel_y", self.curr_vel[1])
                        sim.simSetFloatSignal("vel_z", self.curr_vel[2])
                        self.pr.script_call("createPath@Jaco_target", 1)
                    self.pr.step()
                except KeyboardInterrupt:
                    self.should_stop = True

        finally:
            self.zcmL.stop()
            self.stop()


if __name__ == "__main__":
    simul = Simulation()
    simul.run()
