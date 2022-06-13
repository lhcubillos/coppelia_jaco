import numpy as np
import time
import threading
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity
import sys
import pickle as pk
import signal

from zerocm import ZCM
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

sys.path.insert(1,"/home/xander/coppelia/coppelia_jaco/CoppeliaSim_Edu_V4_3_0_Ubuntu20_04/programming/zmqRemoteApi/clients/python")
###########################################################################
# IMPORTANT: Make the above your path to:
# CoppeliaSim/programming/zmqRemoteApi/clients/python
# If you do not, it will fail to import zmq for hooking CoppeliaSim!
# Can use the Viwer (for data collection) or Edu (for live editing)
###########################################################################
from zmqRemoteApi import RemoteAPIClient

###########################################################################
# This script contains the functions used to inject IMU inputs into
# CoppeliaSim; it can be run before or after running CoppeliaSim and will
# wait for a CoppeliaSim instance if it run first. Uses the ZMQ API to 
# inject a single compressed table of values into CoppeliaSim, containing
# a velocity vector which is then unpacked within CoppeliaSim. The API 
# functions identically to how it is handled in CoppeliaSim's own scripts.
# Do NOT code scene or experiment logic into this or any other external script;
# the injection of code via ZMQ is very slow and thus any writing out of
# CoppeliaSim should be handled inside the scene's own scripts (i.e. inside
# the .ttt file). Try to limit inputs via ZMQ to just velocities, as a single
# setStringSignal call. Takes a .pkl filename as input.
###########################################################################

class Simulation:
    def __init__(self, pca_filename):
        # Initializes remote API client and hooks CS
        self.client = RemoteAPIClient()
        self.client.setStepping(True)
        self.sim = self.client.getObject('sim')
        self.paused = None
        self.jaco_target = self.sim.getScriptHandle(1,'Jaco_target')
        
        # Initializes runtime parameters
        self.curr_vel = [0.0, 0.0, 0.0]
        self.new_vel = [0.0, 0.0, 0.0]
        self.should_stop = False
        self.zcmL = ZCM()
        self.imu_data = None
        self.last_time = None
        
        # Opens PCA model from .pkl file
        self.pca_f = pca_filename
        f = open(self.pca_f,"rb")
        pca_load = pk.load(f)
        self.pca = pca_load[0]
        self.usr_cust = pca_load[1]
        
        # If no usr_cust matrix present, uses identity matrix (i.e. no customization)
        if self.usr_cust is None:
            self.usr_cust = np.identity(2)
        self.pca_cust = np.matmul(self.pca,self.usr_cust)
        
        # Prints the PCA model and usr_cust matrices to the terminal and closes .pkl file
        print(self.pca)
        print(self.usr_cust)
        f.close() 

    def imu_t_callback(self, channel, imu_msg):
        # When receiving imu data, reshape it into the proper form for imu_processing.py
        self.imu_data = np.array([
            imu_msg.imu_values[0].pitch,imu_msg.imu_values[0].roll,\
            imu_msg.imu_values[1].pitch,imu_msg.imu_values[1].roll,\
            imu_msg.imu_values[2].pitch,imu_msg.imu_values[2].roll,\
            imu_msg.imu_values[3].pitch,imu_msg.imu_values[3].roll
        ]).reshape(1,-1)

    def start(self):
        # Starts simulation
        self.sim.startSimulation()
        
        # ZCM
        self.zcmL.subscribe("IMU", imus_t, self.imu_t_callback)
        self.zcmL.start()
        

    def stop(self):
        # When done, stop ZCM and then simulation
        self.zcmL.stop()
        self.sim.stopSimulation()

    def run(self):
        # This method calculates the velocities using imu_processing.py, and then
        # injects them into CS at each step by compressing them and using setStringSignal.
        # It then advances the simulation one step; it is important that this script be 
        # stepped with the simulation to prevent input delay.
        try:
            self.start()
            while not self.should_stop:
                try:
                    start_time = time.time()
                    active = False
                    
                    # If we have new IMU data, calculate the velocity:
                    if self.imu_data is not None:
                        self.new_vel = compute_velocity(self.imu_data,self.pca_cust)
                    
                    # If that velocity is not zero and the process is not shutting down,
                    # compress it and inject it into CS:
                    if (
                        np.linalg.norm(np.array(self.curr_vel) - np.array(self.new_vel))
                        > 0.001
                    ) and (not self.should_stop):
                        self.curr_vel = self.new_vel
                        
                        # Compress signal:
                        velocity_signal = self.sim.packFloatTable(self.new_vel)
                        
                        # Inject signal:
                        self.sim.setStringSignal('velocity',velocity_signal)
                        
                        active = True
                        
                    # Regardless of new data, advance the simulation by one step:
                    self.client.step()
                    
                    #if active:
                        #print(time.time()-start_time)
                except KeyboardInterrupt:
                    # Upon recievning sigint, start stopping the process
                    # A sigint can kill the client connection, so we hook CS again
                    self.client = RemoteAPIClient()
                    self.sim = self.client.getObject('sim')
                    self.should_stop = True
                    

        finally:
            self.stop()


if __name__ == "__main__":
    args = sys.argv
    simul = Simulation(args[1])
    simul.run()
