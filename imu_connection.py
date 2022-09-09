import time
from scipy.spatial.transform import Rotation as R
from OpenGL.GLU import *
from OpenGL.GL import *
import math
import copy
import sys

###########################################################################
# This script takes inputs from the IMU device and broadcasts
# them over ZCM. It is automatically run and shut down by launch_jaco.py.
# Make sure to close it properly; from the commandline this is done by
# giving a sigint. If shut down incorrectly, mutex issues can arise; these
# may require a system restart to clear.
###########################################################################

sys.path.append("./PythonAPIYost/")
import threespace_api as ts_api

import pygame
from pygame.locals import *

from zerocm import ZCM
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

################################################################################
############### First streaming data over a wireless connection ################
################################################################################

# If the COM port is not known or the device type is not known for the 3-Space
# Sensor device, we must do a search for the devices. We can do this by calling
# the getComPorts function which returns a lists of COM port information.
# (both known 3-Space Sensor devices and unknown devices)
# getComPorts also as a parameter called filter that takes a mask that denotes
# what type of 3-Space Sensor device can be found. If filter is not used or set
# to None all connected 3-Space Sensor devices and unknown devices are found.
# Each COM port information is a list containing
# (COM port name, friendly name, 3-Space Sensor device type)
# This example makes use of the filter parameter of getComPorts and just
# searches for Dongle devices.
# device_list = ts_api.getComPorts(filter=ts_api.TSS_FIND_DNG)


# Only one 3-Space Sensor device is needed so we are just going to take the
# first one from the list.

# Make sure to set the port below to the IMU USB device
# PORT = "/dev/ttyACM0"


class IMUStream:
    def __init__(self, frequency):
        self.dng = None
        self.imu_devices = []

        self.latest_data = [None for _ in range(8)]
        self.should_stop = False

        self.zcmL = ZCM()
        self.period = 1.0 / frequency

    def connect(self):
        self.dng = ts_api.TSDongle(com_port=sys.argv[1])
        self.imu_devices = [dev for dev in self.dng]

        for imu_dev in self.imu_devices:
            if imu_dev is None:
                continue
            imu_dev.tareWithCurrentOrientation()
            imu_dev.setStreamingTiming(interval=0, duration=0xFFFFFFFF, delay=0)
            imu_dev.setStreamingSlots(slot0="getTaredOrientationAsEulerAngles")
            # imu_dev.setStreamingSlots(slot0="getTaredOrientationAsQuaternion")
        print(
            "Found {} IMUs connected and started streaming".format(
                len([1 for imu in self.imu_devices if imu is not None])
            )
        )

    def run(self):
        self.connect()

        for imu_dev in self.imu_devices:
            if imu_dev is not None:
                imu_dev.startStreaming()

        try:
            t = time.time()
            while not self.should_stop:
                t += self.period

                latest_data = []
                msg = imus_t()
                msg.utime = int(time.time() * 1000000)
                msg.imu_values = []
                for imu_dev in self.imu_devices:
                    euler_msg = euler_t()
                    if imu_dev is None or imu_dev.stream_last_data is None:
                        latest_data.append(None)
                        euler_msg.available = False
                    else:
                        euler = imu_dev.stream_last_data[1]
                        # This his how they did it in the Matlab program
                        data = [euler[2] * -1, euler[0]]
                        latest_data.append(data)
                        # YPR
                        euler_msg.available = True
                        euler_msg.pitch = data[1]
                        euler_msg.roll = data[0]
                    msg.imu_values.append(euler_msg)
                self.latest_data = copy.copy(latest_data)
                self.zcmL.publish("IMU", msg)
                time.sleep(max(0, t - time.time()))
        except KeyboardInterrupt:
            pass
        finally:
            for imu_dev in self.imu_devices:
                if imu_dev is not None:
                    imu_dev.stopStreaming()
            self.dng.close()

    def show_cube(self):
        self.connect()

        for imu_dev in self.imu_devices:
            if imu_dev is not None:
                imu_dev.startStreaming()
        video_flags = OPENGL | DOUBLEBUF
        pygame.init()
        screen = pygame.display.set_mode((640, 480), video_flags)
        pygame.display.set_caption("PyTeapot IMU orientation visualization")
        self.resizewin(640, 480)
        self.init_graphics()
        frames = 0
        ticks = pygame.time.get_ticks()
        try:
            while True:
                event = pygame.event.poll()
                if event.type == QUIT or (
                    event.type == KEYDOWN and event.key == K_ESCAPE
                ):
                    break
                if (
                    self.imu_devices[0] is not None
                    and self.imu_devices[0].stream_last_data is not None
                ):
                    # TODO: check how to correctly read the data
                    [nx, ny, nz, w] = self.imu_devices[0].stream_last_data[1]
                    self.draw(w, nx, ny, nz)
                    pygame.display.flip()
                    frames += 1
        except KeyboardInterrupt:
            pass
        finally:
            for imu_dev in self.imu_devices:
                if imu_dev is not None:
                    imu_dev.stopStreaming()
            self.dng.close()
        print("fps: %d" % ((frames * 1000) / (pygame.time.get_ticks() - ticks)))

    def resizewin(self, width, height):
        """
        For resizing window
        """
        if height == 0:
            height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, 1.0 * width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def init_graphics(self):
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    def draw(self, w, nx, ny, nz):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0.0, -7.0)

        self.drawText((-2.6, 1.8, 2), "PyTeapot", 18)
        self.drawText(
            (-2.6, 1.6, 2), "Module to visualize quaternion or Euler angles data", 16
        )
        self.drawText((-2.6, -2, 2), "Press Escape to exit.", 16)

        rot = R.from_quat([nx, ny, nz, w])

        # [yaw, pitch, roll] = self.quat_to_ypr([w, nx, ny, nz])
        [roll, yaw, pitch] = rot.as_euler("zyx", degrees=True)
        self.drawText(
            (-2.6, -1.8, 2), "Yaw: %f, Pitch: %f, Roll: %f" % (yaw, pitch, roll), 16
        )
        glRotatef(2 * math.acos(w) * 180.00 / math.pi, -1 * nx, nz, ny)

        glBegin(GL_QUADS)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(1.0, 0.2, -1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(1.0, 0.2, 1.0)

        glColor3f(1.0, 0.5, 0.0)
        glVertex3f(1.0, -0.2, 1.0)
        glVertex3f(-1.0, -0.2, 1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(1.0, -0.2, -1.0)

        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(1.0, 0.2, 1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(-1.0, -0.2, 1.0)
        glVertex3f(1.0, -0.2, 1.0)

        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(1.0, -0.2, -1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(1.0, 0.2, -1.0)

        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(-1.0, 0.2, 1.0)
        glVertex3f(-1.0, 0.2, -1.0)
        glVertex3f(-1.0, -0.2, -1.0)
        glVertex3f(-1.0, -0.2, 1.0)

        glColor3f(1.0, 0.0, 1.0)
        glVertex3f(1.0, 0.2, -1.0)
        glVertex3f(1.0, 0.2, 1.0)
        glVertex3f(1.0, -0.2, 1.0)
        glVertex3f(1.0, -0.2, -1.0)
        glEnd()

    def drawText(self, position, textString, size):
        font = pygame.font.SysFont("Courier", size, True)
        textSurface = font.render(
            textString, True, (255, 255, 255, 255), (0, 0, 0, 255)
        )
        textData = pygame.image.tostring(textSurface, "RGBA", True)
        glRasterPos3d(*position)
        glDrawPixels(
            textSurface.get_width(),
            textSurface.get_height(),
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            textData,
        )

    def quat_to_ypr(self, q):
        yaw = math.atan2(
            2.0 * (q[1] * q[2] + q[0] * q[3]),
            q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3],
        )
        pitch = -math.sin(2.0 * (q[1] * q[3] - q[0] * q[2]))
        roll = math.atan2(
            2.0 * (q[0] * q[1] + q[2] * q[3]),
            q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3],
        )
        pitch *= 180.0 / math.pi
        yaw *= 180.0 / math.pi
        yaw -= -0.13  # Declination at Chandrapur, Maharashtra is - 0 degress 13 min
        roll *= 180.0 / math.pi
        return [yaw, pitch, roll]


if __name__ == "__main__":
    imu_stream = IMUStream(100)
    imu_stream.run()
