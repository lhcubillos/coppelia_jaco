import time
import numpy as np
from zerocm import ZCM
from sklearn.decomposition import PCA
import sys

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque

class CalibrateImu:
    FREQUENCY = 30
    def __init__(self, channel,):
        self.first_time = None
        self.last_msg_timestamp = None
        self.frequency = CalibrateImu.FREQUENCY
        self.f = None
        # ZCM
        self.zcm = ZCM("")
        self.channel = channel
        self.should_stop = False

    def init_process(self,filename):
    	# Open file to save to
        self.f = open(filename,"a")
        # ZCM
        self.zcm.subscribe(self.channel, imus_t, self.handle_messages)

    def handle_messages(self, channel, msg):
        if self.last_msg_timestamp is not None:
            elapsed = time.time() - self.last_msg_timestamp
            if elapsed < 1 / self.frequency:
                return
        self.last_msg_timestamp = time.time()
        if self.first_time is None:
            self.first_time = msg.utime
        if msg.imu_values is not None:
            for i in range(4):
                imu_val = msg.imu_values[i]
                self.f.write(str(imu_val.pitch)+","+str(imu_val.roll))
                if i != 3:
                    self.f.write(",")
            self.f.write("\n")
            

    def run(self,filename):
        self.init_process(filename)
        self.zcm.start()
        try:
            while not self.should_stop:
                continue
        except KeyboardInterrupt:
            self.should_stop = True
        self.f.write("\n")
        self.f.close()
        self.zcm.stop()


# live_update_demo(True)  # 175 fps
# # live_update_demo(False) # 28 fps
if __name__ == "__main__":
    calibrate = CalibrateImu("IMU")
    calibrate.run("imucal")
