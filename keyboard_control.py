from zerocm import ZCM
from pynput.keyboard import Key, Listener
import time
from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t
import math

imu_values = [0.0, 0.0]
zcmL = ZCM()

###########################################################################
# This script contains the functions used for generating fake IMU inputs on
# the ZCM channel with keyboard inputs, for debugging purposes.
# Use arrow keys to generate single-IMU inputs along pitch and roll,
# press the S key to send a zero pitch/roll input (i.e. "stop").
###########################################################################

def on_press(key):
    global imu_values, zcmL
    imu_values = [0.0, 0.0]
    key_pressed = False
    if key == Key.left:
        imu_values[1] = -math.pi / 8
        key_pressed = True
    elif key == Key.right:
        imu_values[1] = math.pi / 8
        key_pressed = True
    elif key == Key.down:
        imu_values[0] = -math.pi / 8
        key_pressed = True
    elif key == Key.up:
        imu_values[0] = math.pi / 8
        key_pressed = True
    elif str(key) == "'s'":
        key_pressed = True

    if key_pressed:
        msg = imus_t()
        euler = euler_t()
        euler.pitch = imu_values[0]
        euler.roll = imu_values[1]
        euler.available = True
        msg.imu_values[0] = euler
        msg.utime = int(time.time() * 1000000)
        zcmL.publish("IMU", msg)


def on_release(key):
    pass


# This publish and sleep are necessary
zcmL.publish("IMU", imus_t())
time.sleep(1)

zcmL.start()
try:
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
except KeyboardInterrupt:
    pass
finally:
    zcmL.stop()
