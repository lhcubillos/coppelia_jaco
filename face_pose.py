import cv2
from headpose import PoseEstimator
import lcm
from lcmtypes.euler_t import euler_t
from lcmtypes.imus_t import imus_t
import numpy as np

lc = lcm.LCM()
est = PoseEstimator()  # load the model
videoCaptureObject = cv2.VideoCapture(0)
while True:
    ret, frame = videoCaptureObject.read()
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow("Capturing Video", image)
    try:
        msg = imus_t()
        euler = euler_t()
        roll, pitch, yawn = est.pose_from_image(image)  # estimate the head pose
        euler.roll = np.deg2rad(roll)
        euler.pitch = np.deg2rad(pitch)
        euler.available = True
        msg.imu_values[0] = euler
        lc.publish("IMU", msg.encode())
        print(roll, pitch, yawn)
    except ValueError:
        pass
    if cv2.waitKey(1) & 0xFF == ord("q"):
        videoCaptureObject.release()
        cv2.destroyAllWindows()
