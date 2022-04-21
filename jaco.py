import numpy as np
import time
import threading
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity
import sys
import pickle as pk
import signal

# import lcm
# from lcmtypes.imus_t import imus_t
# from lcmtypes.euler_t import euler_t
from zerocm import ZCM
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

sys.path.insert(1,"/home/xander/coppelia/coppelia_jaco/CoppeliaSim_Edu_V4_3_0_Ubuntu20_04/programming/zmqRemoteApi/clients/python")
# Make this your path to CoppeliaSim/programming/zmqRemoteApi/clients/python

from zmqRemoteApi import RemoteAPIClient

class JacoArm:
    def __init__(self, arm, gripper):
        self.arm = arm
        # self.gripper = gripper


class Simulation:
    def __init__(self, pca_filename):
        self.client = RemoteAPIClient()
        self.client.setStepping(True)
        self.sim = self.client.getObject('sim')
        self.paused = None
        self.jaco_target = self.sim.getScriptHandle(1,'Jaco_target')
        self.curr_vel = [0.0, 0.0, 0.0]
        self.new_vel = [0.0, 0.0, 0.0]
        self.should_stop = False
        self.zcmL = ZCM()
        self.imu_data = None
        
        self.last_time = None
        
        self.pca_f = pca_filename
        f = open(self.pca_f,"rb")
        
        pca_load = pk.load(f)
        self.pca = pca_load[0]
        self.usr_cust = pca_load[1]
        
        if self.usr_cust is None:
            self.usr_cust = np.identity(2)
        self.pca_cust = np.matmul(self.pca,self.usr_cust)
        print(self.pca)
        print(self.usr_cust)
        f.close() 

    def imu_t_callback(self, channel, imu_msg):
        self.imu_data = np.array([
            imu_msg.imu_values[0].pitch,imu_msg.imu_values[0].roll,\
            imu_msg.imu_values[1].pitch,imu_msg.imu_values[1].roll,\
            imu_msg.imu_values[2].pitch,imu_msg.imu_values[2].roll,\
            imu_msg.imu_values[3].pitch,imu_msg.imu_values[3].roll
        ]).reshape(1,-1)

    def start(self):
        # ZCM
        self.sim.startSimulation()
        
        self.zcmL.subscribe("IMU", imus_t, self.imu_t_callback)
        self.zcmL.start()
        

    def stop(self):
        self.zcmL.stop()
        self.sim.stopSimulation()

    def run(self):
        try:
            self.start()
            
            while not self.should_stop:
                try:
                    # print(self.imu_data)
                    start_time = time.time()
                    active = False
                    if self.imu_data is not None:
                        self.new_vel = compute_velocity(self.imu_data,self.pca_cust)
                    if (
                        np.linalg.norm(np.array(self.curr_vel) - np.array(self.new_vel))
                        > 0.001
                    ) and (not self.should_stop):
                        self.curr_vel = self.new_vel
                        
                        velocity_signal = self.sim.packFloatTable(self.new_vel)
                        
                        self.sim.setStringSignal('velocity',velocity_signal)
                        
                        active = True
                        #self.sim.setFloatSignal("vel_x", self.curr_vel[0])
                        #self.sim.setFloatSignal("vel_y", self.curr_vel[1])
                        #self.sim.setFloatSignal("vel_z", self.curr_vel[2])
                        #self.sim.callScriptFunction("createPath@/Jaco_target", self.jaco_target)

                    self.client.step()
                    
                    #if active:
                        #print(time.time()-start_time)
                except KeyboardInterrupt:
                    self.client = RemoteAPIClient()
                    self.sim = self.client.getObject('sim')
                    self.should_stop = True
                    

        finally:
            self.stop()


if __name__ == "__main__":
    args = sys.argv
    simul = Simulation(args[1])
    simul.run()
