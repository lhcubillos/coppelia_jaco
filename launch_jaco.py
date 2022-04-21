import time
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
import numpy as np
from zerocm import ZCM
import sys
import pickle as pk
import tkinter as tk
import subprocess
import signal
import os

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque
from imu_processing import compute_velocity

class JacoUI:
    def __init__(self):
        self.process = subprocess.Popen(['python','imu_connection.py'])
        self.coppelia = None
        self.custom = None
        self.calib = None
        self.jaco_p = None
        self.window = None
        self.button1 = None
        self.button2 = None
        self.button3 = None
        self.button4 = None
        
    def press1(self):
        filename = tk.filedialog.askopenfilename(initialdir = ".",
                                          title = "Choose output filename",
                                          filetypes = (("user customization files",
                                                        "*.pkl*"),
                                                       ("all files",
                                                        "*.*")))
        self.calib = subprocess.Popen(['python','imu_calibrate.py',filename])
        
    def press2(self):
        filename = tk.filedialog.askopenfilename(initialdir = ".",
                                          title = "Choose customization file",
                                          filetypes = (("user customization files",
                                                        "*.pkl*"),
                                                       ("all files",
                                                        "*.*")))
        self.custom = subprocess.Popen(['python','usr_customize.py',filename])
        
    def press3(self):
        if self.coppelia is None:
            self.coppelia = subprocess.Popen(['/home/xander/coppelia/coppelia_jaco/CoppeliaSim_Edu_V4_3_0_Ubuntu20_04/coppeliaSim','/home/xander/coppelia/coppelia_jaco/coppelia_jaco/scene_jaco_circle.ttt'])
        if self.jaco_p is None:
            filename = tk.filedialog.askopenfilename(initialdir = ".",
                                              title = "Choose customization file",
                                              filetypes = (("user customization files",
                                                            "*.pkl*"),
                                                           ("all files",
                                                            "*.*")))
            self.jaco_p = subprocess.Popen(['python','jaco.py',filename])
        else:
            self.jaco_p.terminate()
            filename = tk.filedialog.askopenfilename(initialdir = ".",
                                              title = "Choose customization file",
                                              filetypes = (("user customization files",
                                                            "*.pkl*"),
                                                           ("all files",
                                                            "*.*")))
            self.jaco_p = subprocess.Popen(['python','jaco.py',filename])
            
        
    def press4(self):
        self.window.destroy()
        
    def init_process(self):
        self.window = tk.Tk()
        self.window.title('JACO Simulator Launcher')
        self.window.geometry('500x500')
        self.button1 = tk.Button(self.window,text='Start calibration',command=self.press1)
        self.button2 = tk.Button(self.window,text='Launch customizer',command=self.press2)
        self.button3 = tk.Button(self.window,text='Run circles experiment',command=self.press3)
        self.button4 = tk.Button(self.window,text='Close Launcher',command=self.press4)
        self.button1.pack()
        self.button2.pack()
        self.button3.pack()
        self.button4.pack()
    
    def run(self):
        self.init_process()
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            pass
        if self.calib is not None:
            self.calib.terminate()
        if self.custom is not None:
            self.custom.terminate()
        if self.coppelia is not None:
            self.coppelia.terminate()
        if self.jaco_p is not None:
            self.jaco_p.terminate()
        if self.process is not None:
            self.process.send_signal(signal.SIGINT)
        sys.exit()


# live_update_demo(True)  # 175 fps
# # live_update_demo(False) # 28 fps
if __name__ == "__main__":
    ui = JacoUI()
    ui.run()
