import time
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
import numpy as np
from zerocm import ZCM
import sys
import pickle as pk
import tkinter as tk
import threading

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque
from imu_processing import compute_velocity


###########################################################################
# This script is used to run the user customization UI and processing.
# Takes a .pkl filename as input, outputs the customized PCA model as 
# <filename>_cust.pkl. Can adjust the sensitivity for each principle axis,
# reverse the directions of the axes, or switch the order of the axes.
# Has a liveplot display that allows for live feedback. Only saves a new file if
# "Accept" is clicked, otherwise discards changes on closing. Can load existing
# customized files and will identify existing customizations.
#
# TODO: Full commentary on this script
###########################################################################


class LivePlotCust:
    FREQUENCY = 30

    def __init__(self, channel, filename):
        self.lock = threading.Lock()
        self.fig = None
        self.ax = None
        self.dot = None
        self.axbackground = None
        self.maxspeed = 0.2
        self.vel_tolerance = 0.2
        self.y = 0.0
        self.x = 0.0
        self.first_time = None
        self.last_msg_timestamp = None
        self.frequency = LivePlotCust.FREQUENCY
        self.filename = filename
        f = open(filename,"rb")
        pca_load = pk.load(f)
        self.pca = pca_load[0]
        self.cust = pca_load[1]
        if self.cust is None:
            self.cust = np.identity(2)
        f.close
        self.pca_cust = np.matmul(self.pca,self.cust)

        self.canvas = None
        self.window = None
        self.slider1 = None
        self.slidetext1 = None
        self.slider2 = None
        self.slidetext2 = None
        self.slider3 = None
        self.slidetext3 = None

        if self.cust[0,0] == 0:
            self.reverse = True
        else:
            self.reverse = False
        if np.sign(self.cust[0,0]+self.cust[0,1]) == -1:
            self.flip1 = True
        else:
            self.flip1 = False
        if np.sign(self.cust[1,0]+self.cust[1,1]) == -1:
            self.flip2 = True
        else:
            self.flip2 = False
        self.accept = False
        # ZCM
        self.zcm = ZCM("")
        self.channel = channel

    def parse1(self,event):
        text = float(self.slidetext1.get("0.0","end").strip())
        self.slider1.set(text)
        self.slidetext1.delete("0.0","end")
        self.slidetext1.delete("0.0")
        return 'break'
        
    def parse2(self,event):
        text = float(self.slidetext2.get("0.0","end").strip())
        self.slider2.set(text)
        self.slidetext2.delete("0.0","end")
        self.slidetext2.delete("0.0")
        return 'break'
    
    def parse3(self,event):
        text = float(self.slidetext3.get("0.00","end").strip())
        self.slider3.set(text)
        self.slidetext3.delete("0.00","end")
        self.slidetext3.delete("0.00")
        return 'break'
        
    def press1(self):
        if self.reverse:
            self.reverse = False
        else:
            self.reverse = True
        
    def press2(self):
        if self.flip1:
            self.flip1 = False
        else:
            self.flip1 = True
        
    def press3(self):
        if self.flip2:
            self.flip2 = False
        else:
            self.flip2 = True
        
    def press4(self):
        self.accept = True
        out_f = open(self.filename[:-4]+"_cust.pkl","wb")
        pk.dump([self.pca,self.cust,self.vel_tolerance],out_f)
        print("Saved user customizations to "+self.filename[:-4]+"_cust.pkl")
        out_f.close()
        self.window.destroy()
    
    def press5(self):
        self.accept = False
        self.window.destroy()
        
    def init_process(self):
        self.window = tk.Tk()
        self.window.title('User Customization')
        self.window.geometry('1000x500')
        
        self.slider1 = tk.Scale(self.window,label='Sensitivity 1',digits=3,resolution=0.0,from_=0.1,to=10.0,orient='horizontal')
        self.slider1.set(abs(self.cust[0,0])+(self.cust[0,1]))
        self.slider2 = tk.Scale(self.window,label='Sensitivity 2',digits=3,resolution=0.0,from_=0.1,to=10.0,orient='horizontal')
        self.slider2.set(abs(self.cust[1,0])+(self.cust[1,1]))
        self.slider3 = tk.Scale(self.window,label='Toleranc_mps',digits=3,resolution=0.00,from_=0.01,to=1.00,orient='horizontal')
        self.slider3.set(abs(0.20))
        self.slidetext1 = tk.Text(self.window,width=10,height=1)
        self.slidetext1.bind("<Return>",self.parse1)
        self.slidetext2 = tk.Text(self.window,width=10,height=1)
        self.slidetext2.bind("<Return>",self.parse2)
        self.slidetext3 = tk.Text(self.window,width=10,height=1)
        self.slidetext3.bind("<Return>",self.parse3)
        
        self.button1 = tk.Button(self.window,text='Switch motions 1 and 2',command=self.press1)
        self.button2 = tk.Button(self.window,text='Reverse axis 1',command=self.press2)
        self.button3 = tk.Button(self.window,text='Reverse axis 2',command=self.press3)
        self.button4 = tk.Button(self.window,text='Accept',command=self.press4)
        self.button5 = tk.Button(self.window,text='Cancel',command=self.press5)
        self.slider1.pack()
        self.slidetext1.pack()
        self.slider2.pack()
        self.slidetext2.pack()
        self.slider3.pack()
        self.slidetext3.pack()
        self.button1.pack()
        self.button2.pack()
        self.button3.pack()
        self.button4.pack()
        self.button5.pack()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        (self.dot,) = self.ax.plot([],marker="x", markersize=15, markeredgecolor="black", markerfacecolor="black")
        self.ax.set_xlim(-self.maxspeed-0.1,self.maxspeed+0.1)
        self.ax.set_ylim(-self.maxspeed-0.1,self.maxspeed+0.1)
        
        #self.axbackground = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
        #plt.show(block=False)
        

        
        # ZCM
        self.zcm.subscribe(self.channel, imus_t, self.handle_messages)

    def handle_messages(self, channel, msg):
        with self.lock:
            sense1 = float(self.slider1.get())
            sense2 = float(self.slider2.get())
            self.vel_tolerance = float(self.slider3.get())
        
            self.cust = np.array([[sense1,0.0],[0.0,sense2]])
        
            if self.reverse:
                self.cust = np.matmul(self.cust,np.array([[0.0,1.0],[1.0,0.0]]))
            if self.flip1:
                self.cust = np.matmul(self.cust,np.array([[-1.0,0.0],[0.0,1.0]]))
            if self.flip2:
                self.cust = np.matmul(self.cust,np.array([[1.0,0.0],[0.0,-1.0]]))
        
            self.pca_cust = np.matmul(self.pca,self.cust)
            if self.last_msg_timestamp is not None:
                elapsed = time.time() - self.last_msg_timestamp
                if elapsed < 1 / self.frequency:
                    return
            self.last_msg_timestamp = time.time()
            if self.first_time is None:
                self.first_time = msg.utime
            if msg.imu_values[0] is not None:
                self.imu_data = np.array([
                msg.imu_values[0].pitch,msg.imu_values[0].roll,\
                msg.imu_values[1].pitch,msg.imu_values[1].roll,\
                msg.imu_values[2].pitch,msg.imu_values[2].roll,\
                msg.imu_values[3].pitch,msg.imu_values[3].roll
            ]).reshape(1,-1)
                [self.x,__,self.y] = compute_velocity(self.imu_data,self.pca_cust,self.vel_tolerance)
                self.dot.set_data(np.array(self.x), np.array(self.y))
                # self.canvas.draw()
                # self.window.update()
    
    def draw_plot(self):
        with self.lock:
            self.canvas.draw()
            self.window.after(LivePlotCust.FREQUENCY, self.draw_plot)
    
    def run(self):
        self.init_process()
        self.zcm.start()
        self.draw_plot()
        self.window.update()
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            pass
        self.zcm.stop()
        if self.accept:
            pass
        sys.exit()


# live_update_demo(True)  # 175 fps
# # live_update_demo(False) # 28 fps
if __name__ == "__main__":
    args = sys.argv
    lp = LivePlotCust("IMU",args[1])
    lp.run()
