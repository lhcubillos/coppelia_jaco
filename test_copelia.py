from pyrep import PyRep
from pyrep.backend import sim, utils
from pyrep.robots.arms.jaco import Jaco
from pyrep.robots.end_effectors.jaco_gripper import JacoGripper
import numpy as np
import time
from multiprocessing import Process
from pynput.keyboard import Key, Listener
from imu_processing import compute_velocity
import sys
import pickle as pk
import threading

class JacoArm:
    def __init__(self, arm, gripper):
        self.arm = arm
        # self.gripper = gripper


class Simulation:
    def __init__(self, scene_name="scene_jaco.ttt"):
        self.pr = None
        self.jaco = None

        self.scene_name = scene_name
        self.should_stop = False
        self.process = Process(target=self.run_cope,args=())


    def start(self):

        # pygame.init()
        # Launch CS
        
        try:
            self.process.start()
        except KeyboardInterrupt:
                self.should_stop = True
                print("closing from start...")

    def run_cope(self):
        self.pr = PyRep()
        self.pr.launch(self.scene_name)
        self.pr.start()

        self.jaco = JacoArm(Jaco(), None)
        while not self.should_stop:
            try:
                self.pr.step()
            except KeyboardInterrupt:
                self.should_stop = True
                print("closing from process...")
        self.stop()
        
    def stop(self):
        self.pr.stop()
        # self.pr.shutdown()

    def run(self):
        
        self.start()
            
        self.process.join()
            

if __name__ == "__main__":
    simul = Simulation()
    simul.run()
