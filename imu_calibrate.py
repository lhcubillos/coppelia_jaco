import time
import numpy as np
from zerocm import ZCM
from sklearn.decomposition import PCA
import sys
import pickle as pk
import tkinter as tk
import subprocess
from threading import *

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque

###########################################################################
# This script contains the functions used to calibrate a new PCA model from
# IMU inputs. Takes a filename as input and outputs .calib and .pkl files,
# containing the calibration data and the PCA model respectively.
# Automatically launches the customizer when finished.
###########################################################################

class CalibrateImu:
    # Frequency for collecting IMU data
    FREQUENCY = 30
    def __init__(self, channel,):
        # takes input argument as filename, defaults to "test" if no argument given
        self.filename = "test.pkl"
        
        # initialize UI elements
        self.window = None
        self.text = None
        self.button = None
        self.button2 = None
        
        # initialize runtime parameters
        self.first_time = None        
        self.running = False
        self.cancelled = False
        self.start_time = None
        self.stop_time = 60.0
        self.last_msg_timestamp = None
        self.frequency = CalibrateImu.FREQUENCY
        self.f = None

        # initialize ZCM
        self.zcm = ZCM("")
        self.channel = channel
        self.should_stop = False
        
    def parseText(self,event):
        # parse UI text input
        self.runCalib()
        return 'break'
    
    def threading(self):
        t1=Thread(target=self.runCalib)
        t1.start()
        
    def runCalib(self):
        # upon clicking the calibrate button, disables UI
        self.button["state"] = "disabled"
        self.text["state"] = "disabled"
        textParse = float(self.text.get("0.0","end").strip())
        self.stop_time = textParse
        self.start_time = time.time()
        self.running = True
        # collect UI data and save it to filename.calib
        try:
            while not self.should_stop:
                if (time.time() - self.start_time) >= self.stop_time:
                    self.should_stop = True
                if self.should_stop:
                    break
        except KeyboardInterrupt:
            self.should_stop = True
        self.zcm.stop()
        if self.cancelled:
            self.window.destroy()
            return
        self.f.write("\n")
        self.f.close()
        
        # after data collection, process data via PCA to obtain first two principle components
        # then, build the PCA transformation matrix, normalize/center them, and save to filename.pkl
        data = np.genfromtxt(filename[:-4]+".calib",delimiter=",")
        data_pca = PCA(n_components=2)
        try:
            data_pca.fit(data)
        except:
            self.zcm.stop()
            self.window.destroy()
            sys.exit()

        pca_transform=data_pca.transform(np.identity(8))
        norms = np.linalg.norm(pca_transform,2,0)
        variances = data_pca.explained_variance_
        [n,m] = np.shape(pca_transform)
        pca_normalized = pca_transform
        for i in range(n):
            for j in range(m):
                pca_normalized[i,j] = (pca_transform[i,j]/norms[j])/np.sqrt(variances[j])
        rest = [0.0, 0.0, 0.0]
        pca_dump = [pca_normalized, None, 0.2, rest]
        f = open(filename,"wb")
        pk.dump(pca_dump, f)
        f.close()
        
        # finally, close the calibration window and launch the customizer automatically on filename.pkl
        self.window.destroy()

    def cancelCalib(self):
        # if cancel is clicked, either stop running or close the window without running
        if not self.running:
            self.window.destroy()
        else:
            self.should_stop = True
            self.cancelled = True
            self.zcm.stop()
            self.f.close()
            self.window.destroy()

    def init_process(self,filename):
    	# Open file to save to
        self.filename = filename
        self.f = open(self.filename[:-4]+".calib",'w')
        
        # Build UI
        self.window = tk.Tk()
        self.window.title('PCA Calibration')
        self.label = tk.Label(self.window,text="Calibration Duration (Default 60.0 seconds)")
        self.text = tk.Text(self.window,width=10,height=1)
        self.text.insert("0.0","60.0")
        self.text.bind("<Return>",self.parseText)
        self.button = tk.Button(self.window,text='Start Calibration',command=self.threading)
        self.button2 = tk.Button(self.window,text='Cancel',command=self.cancelCalib)
        self.label.pack()
        self.text.pack()
        self.button.pack()
        self.button2.pack()
        self.window.geometry('800x500')
        # ZCM
        self.zcm.subscribe(self.channel, imus_t, self.handle_messages)

    def handle_messages(self, channel, msg):
        # ZCM handler, saves every IMU input during calibration
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
        self.window.mainloop()
        if not self.cancelled:
            print("Calibration done, opening customizer")
            subprocess.Popen(['python3','usr_customize.py',self.filename])
        sys.exit()

if __name__ == "__main__":
    # Filename is recieved as first argument
    filename = sys.argv[1]
    print(filename)
    calibrate = CalibrateImu("IMU")
    calibrate.run(filename)
