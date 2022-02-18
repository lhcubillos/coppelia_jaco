import time
from matplotlib import pyplot as plt
import numpy as np
from zerocm import ZCM
import sys

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque


class LivePlot:
    FREQUENCY = 30

    def __init__(self, channel):
        self.fig = None
        self.ax = None
        self.line1 = None
        self.line2 = None
        self.axbackground = None
        maxsize = 500
        self.y1 = deque(maxlen=maxsize)
        self.y2 = deque(maxlen=maxsize)
        self.x = deque(maxlen=maxsize)
        self.first_time = None
        self.last_msg_timestamp = None
        self.frequency = LivePlot.FREQUENCY

        # ZCM
        self.zcm = ZCM("")
        self.channel = channel

    def init_process(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        (self.line1,) = self.ax.plot([], lw=2)
        (self.line2,) = self.ax.plot([], lw=2)
        self.axbackground = self.fig.canvas.copy_from_bbox(self.ax.bbox)
        self.fig.canvas.draw()
        plt.show(block=False)
        plt.legend(["Pitch", "Roll"])
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
        # FIXME: for now, only plotting first IMU
        if msg.imu_values[0] is not None:
            self.x.append((msg.utime - self.first_time) / 1000000)
            imu_val = msg.imu_values[0]
            self.y1.append(imu_val.pitch)
            self.y2.append(imu_val.roll)

            # Update lines
            self.line1.set_data(np.array(self.x), np.array(self.y1))
            self.line2.set_data(np.array(self.x), np.array(self.y2))
            self.ax.set_xlim(min(self.x), max(self.x))
            self.ax.set_ylim(
                min(min(self.y1), min(self.y2)), max(max(self.y1), max(self.y2))
            )

    def run(self):
        self.init_process()
        self.zcm.start()
        try:
            while True:
                # self.fig.canvas.restore_region(self.axbackground)
                # self.ax.draw_artist(self.line1)
                # self.ax.draw_artist(self.line2)
                # self.fig.canvas.blit(self.ax.bbox)
                self.fig.canvas.draw()

                self.fig.canvas.flush_events()

        except KeyboardInterrupt:
            pass
        self.zcm.stop()


# live_update_demo(True)  # 175 fps
# # live_update_demo(False) # 28 fps
if __name__ == "__main__":
    lp = LivePlot("IMU")
    lp.run()
