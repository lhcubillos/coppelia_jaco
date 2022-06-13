import numpy as np
import time
import threading
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity

from zerocm import ZCM
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t
import sys
import pickle as pk

###########################################################################
# This script is a simple test for the PCA system, and should be kept
# identical to the processing executed in jaco.py. Takes a .pkl filename as input,
# and simply outputs calculated velocities from ZCM IMU data to the terminal as a vector.
###########################################################################

class PCATest:
    def __init__(self,filename):
        self.filename = filename
        f = open(filename,"rb")
        pca_load = pk.load(f)
        self.pca = pca_load[0]
        self.cust = pca_load[1]
        if self.cust is None:
            self.cust = np.identity(2)*1
        f.close
        self.pca_cust = np.matmul(self.pca,self.cust)
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
                        self.new_vel = compute_velocity(self.imu_data,self.pca_cust)
                        total_vel = np.sqrt(np.power(self.new_vel[0],2) + np.power(self.new_vel[1],2) + np.power(self.new_vel[2],2))
                        print(str(self.new_vel)+str(total_vel)+"        ",end="\r")
                    
                except KeyboardInterrupt:
                    self.should_stop = True

        finally:
            self.zcmL.stop()


if __name__ == "__main__":
    args = sys.argv
    simul = PCATest(args[1])
    simul.run()
