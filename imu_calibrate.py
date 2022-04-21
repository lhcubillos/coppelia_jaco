import time
import numpy as np
from zerocm import ZCM
from sklearn.decomposition import PCA
import sys
import pickle as pk
import tkinter as tk
import subprocess

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque

class CalibrateImu:
    FREQUENCY = 30
    def __init__(self, channel,):
        self.filename = "test.pkl"
        self.first_time = None
        self.window = None
        self.text = None
        self.button = None
        self.button2 = None
        self.running = False
        self.start_time = None
        self.stop_time = 60.0
        self.last_msg_timestamp = None
        self.frequency = CalibrateImu.FREQUENCY
        self.f = None
        # ZCM
        self.zcm = ZCM("")
        self.channel = channel
        self.should_stop = False
        
    def parseText(self,event):
        self.runCalib()
        return 'break'
        
    def runCalib(self):
        self.button["state"] = "disabled"
        self.text["state"] = "disabled"
        textParse = float(self.text.get("0.0","end").strip())
        self.stop_time = textParse
        self.start_time = time.time()
        self.running = True
        try:
            while not self.should_stop:
                if (time.time() - self.start_time) >= self.stop_time:
                    self.should_stop = True  
        except KeyboardInterrupt:
            self.should_stop = True
        self.zcm.stop()
        self.f.write("\n")
        self.f.close()
        data = np.genfromtxt(filename[:-4],delimiter=",")
        data_pca = PCA(n_components=2)
        data_pca.fit(data)
        pca_transform=data_pca.transform(np.identity(8))
        norms = np.linalg.norm(pca_transform,2,0)
        variances = data_pca.explained_variance_
        [n,m] = np.shape(pca_transform)
        pca_normalized = pca_transform
        for i in range(n):
            for j in range(m):
                pca_normalized[i,j] = (pca_transform[i,j]/norms[j])/np.sqrt(variances[j])
        pca_dump = [pca_normalized, None]
        f = open(filename,"wb")
        pk.dump(pca_dump, f)
        
        f.close
        #self.should_stop = False
        #self.running = False
        #self.button["state"] = "normal"
        #self.text["state"] = "normal"
        self.window.destroy()
        print("Calibration done, opening customizer")
        subprocess.Popen(['python','usr_customize.py',self.filename])
        sys.exit()

    def cancelCalib(self):
        if not self.running:
            self.window.destroy()
        else:
            self.should_stop = True
        
    def init_process(self,filename):
    	# Open file to save to
        self.filename = filename
        self.f = open(self.filename[:-4],'w')
        self.window = tk.Tk()
        self.window.title('PCA Calibration')
        self.label = tk.Label(self.window,text="Calibration Duration (Default 60.0 seconds)")
        self.text = tk.Text(self.window,width=10,height=1)
        self.text.insert("0.0","60.0")
        self.text.bind("<Return>",self.parseText)
        self.button = tk.Button(self.window,text='Start Calibration',command=self.runCalib)
        self.button2 = tk.Button(self.window,text='Cancel',command=self.cancelCalib)
        self.label.pack()
        self.text.pack()
        self.button.pack()
        self.button2.pack()
        self.window.geometry('320x100')
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
        self.window.mainloop()
        
        
        
        

if __name__ == "__main__":
    filename = sys.argv[1]
    print(filename)
    calibrate = CalibrateImu("IMU")
    calibrate.run(filename)

