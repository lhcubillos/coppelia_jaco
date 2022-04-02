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


class PCATest:
    def __init__(self):
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

    def run(self):
        try:
            self.start()
            start = time.time()
            while not self.should_stop:
                try:
                    # print(self.imu_data)
                    # TODO: requires all four imus for now
                    if self.imu_data is not None:
                        self.new_vel = compute_velocity(self.imu_data)
                        print(str(self.new_vel)+"                          ",end="\r")
                    
                except KeyboardInterrupt:
                    self.should_stop = True

        finally:
            self.zcmL.stop()


if __name__ == "__main__":
    simul = PCATest()
    simul.run()
