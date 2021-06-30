from pyrep import PyRep
from pyrep.backend import sim, utils
from pyrep.robots.arms.jaco import Jaco
from pyrep.robots.end_effectors.jaco_gripper import JacoGripper
import numpy as np
import time
import threading
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity

import lcm
from lcmtypes.imus_t import imus_t
from lcmtypes.euler_t import euler_t


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
        self.lc = lcm.LCM()
        self.imu_data = [None for _ in range(4)]
        self.lcm_thread = threading.Thread(target=self.lcm_loop, daemon=True)

        # # IMU streamer
        # self.imu_streamer = IMUStream()
        # self.imu_thread = threading.Thread(target=self.imu_streamer.run, daemon=True)

    def lcm_loop(self):
        while True:
            self.lc.handle()

    def imu_t_callback(self, channel, data):
        imu_msg = imus_t.decode(data)
        self.imu_data = [
            [v.pitch, v.roll] if v.available else None for v in imu_msg.imu_values
        ]

    def capture_keyboard(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
        self.should_stop = True

    def on_press(self, key):
        velocity = [0.0, 0.0, 0.0]
        if key == Key.left:
            velocity[1] = -0.1
        elif key == Key.right:
            velocity[1] = 0.1
        elif key == Key.down:
            velocity[2] = -0.1
        elif key == Key.up:
            velocity[2] = 0.1

        if velocity != self.curr_vel:
            self.new_vel = velocity

    def on_release(self, key):
        if key == Key.left or key == Key.right or key == Key.down or key == Key.up:
            self.new_vel = [0.0, 0.0, 0.0]

    def start(self):
        # LCM
        self.lc.subscribe("IMU", self.imu_t_callback)
        self.lcm_thread.start()
        # IMU stream

        # pygame.init()
        # Launch CS
        self.pr.launch(self.scene_name)
        # Start simulation
        self.pr.start()

        # Get arm from simulation
        self.jaco = JacoArm(Jaco(), None)
        # self.keys_thread.start()

    def stop(self):
        # self.pr.stop()
        # self.pr.shutdown()
        pass

    def run(self):
        try:
            self.start()
            start = time.time()
            while time.time() - start < 3:
                self.pr.step()
            while not self.should_stop:
                try:
                    # print(self.imu_data)
                    # FIXME: remove this
                    self.new_vel = compute_velocity(self.imu_data)
                    # if self.imu_data[0] is not None:
                    #     if self.imu_data[0][1] > -0.02 and self.imu_data[0][1] < 0.02:
                    #         self.new_vel = [0.0, 0.0, 0.0]
                    #     elif self.imu_data[0][1] >= 0.01:
                    #         self.new_vel = [0.0, 0.1, 0.0]
                    #     else:
                    #         self.new_vel = [0, -0.1, 0]
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
                    # self.imu_streamer.should_stop = True

        finally:
            self.stop()


if __name__ == "__main__":
    simul = Simulation()
    simul.run()
