import numpy as np
from sklearn.decomposition import PCA

TOLERANCE = 0.02
MAX_SPEED = 0.5


def compute_velocity(imu_data):
    # FIXME: only using the first IMU for now
    vel = [0.0, 0.0, 0.0]
    if imu_data[0] is not None:
        # Pitch
        if value_within_tolerance(imu_data[0][0]):
            vel[2] = 0.0
        else:
            vel[2] = get_speed(imu_data[0][0])
        # Roll
        if value_within_tolerance(imu_data[0][1]):
            vel[1] = 0.0
        else:
            vel[1] = get_speed(imu_data[0][1])
    return vel


def value_within_tolerance(value):
    if value > -TOLERANCE and value < TOLERANCE:
        return True
    return False


def get_speed(value):
    percentage = abs(value) / (np.pi / 2)
    return np.sign(value) * percentage * MAX_SPEED
