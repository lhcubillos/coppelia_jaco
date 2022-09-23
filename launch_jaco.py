
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

###########################################################################
# This script contains the functions used to run the launcher. Simply run
# this script from a commandline to start the launcher. Automatically starts
# and safely closes imu_connection.py on launching (make sure to use the 
# "Close Launcher" button and not the red X in the corner to avoid mutex issues).
# Can launch calibration, customization, and jaco.py (along with CS) from this launcher.
# All other scripts are contained within subprocesses that are safely killed
# using the "Close Launcher" button. Will only launch one instance of CS;
# if one is already open within the launcher, will not open another.
# More buttons can be added as needed for other experiments/scenes/etc.
###########################################################################

curCwd = os.getcwd()

class JacoUI:
    def __init__(self):
        # Initialize subprocesses and UI
        self.process = subprocess.Popen(['python3','imu_connection.py', sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"])
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
        # Ask for filename for new .calib and .pkl files
        # Then, launches the calibration routine
        # Automatically launches the customizer when finished
        filename = tk.filedialog.asksaveasfilename(initialdir = ".",
                                          title = "Choose output filename",
                                          filetypes = (("user customization files",
                                                        "*.pkl*"),
                                                       ("all files",
                                                        "*.*")))
        self.calib = subprocess.Popen(['python3','imu_calibrate.py',filename])
        
    def press2(self):
        # Ask for filename for existing .pkl file
        # Then, launches the customization routine
        filename = tk.filedialog.askopenfilename(initialdir = ".",
                                          title = "Choose customization file",
                                          filetypes = (("user customization files",
                                                        "*.pkl*"),
                                                       ("all files",
                                                        "*.*")))
        self.custom = subprocess.Popen(['python3','usr_customize.py',filename])
        
    def press3(self):
        # Check if CS is running in launcher; if not, open it.
        # Check if jaco.py is running in launcher; if not, start it. If so, kill and restart it.
        if self.coppelia is None:
            self.coppelia = subprocess.Popen([curCwd + '/../CoppeliaSim/coppeliaSim',curCwd + '/scene_jaco_circle.ttt'])
        if self.jaco_p is None:
            filename = tk.filedialog.askopenfilename(initialdir = ".",
                                              title = "Choose customization file",
                                              filetypes = (("user customization files",
                                                            "*.pkl*"),
                                                           ("all files",
                                                            "*.*")))
            self.jaco_p = subprocess.Popen(['python3','jaco.py',filename])
        else:
            self.jaco_p.terminate()
            filename = tk.filedialog.askopenfilename(initialdir = ".",
                                              title = "Choose customization file",
                                              filetypes = (("user customization files",
                                                            "*.pkl*"),
                                                           ("all files",
                                                            "*.*")))
            self.jaco_p = subprocess.Popen(['python3','jaco.py',filename])
            
        
    def press4(self):
        # Kill the UI window, allowing subprocesses to be safely closed
        self.window.destroy()
        
    def init_process(self):
        # Build the UI
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
            # Run the tkinter logic for the UI window
            self.window.mainloop()
        except KeyboardInterrupt:
            pass
        # When window terminates, safely close every subprocess and exit
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
