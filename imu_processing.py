import numpy as np
from sklearn.decomposition import PCA
import pickle as pk

TOLERANCE = 0.08
MAX_SPEED = 0.2


def compute_velocity(imu_data):
    imu_pca = pk.load(open("imu_pca.pkl","rb"))
    imu_vel = imu_pca.transform(imu_data)[0]
    vel = [0.0, 0.0, 0.0]
    # Arbitratily deciding component 1 is Z, component 2 is Y
    if imu_data is not None:
        # Z component
        if value_within_tolerance(imu_vel[0]):
            vel[2] = 0.0
        else:
            vel[2] = get_speed(imu_vel[0])*0.2
        # Y component
        if value_within_tolerance(imu_vel[1]):
            vel[1] = 0.0
        else:
            vel[1] = get_speed(imu_vel[1])
    return vel


def value_within_tolerance(value):
    if value > -TOLERANCE and value < TOLERANCE:
        return True
    return False


def get_speed(value):
    percentage = abs(value) / (np.pi / 2)
    return np.sign(value) * percentage * MAX_SPEED
