import numpy as np
from sklearn.decomposition import PCA
import pickle as pk

TOLERANCE = 0.2
MAX_SPEED = 0.2


def compute_velocity(imu_data,pca):
    imu_vel = np.matmul(pca.T,imu_data.T)
    vel = [0.0, 0.0, 0.0]
    # Arbitratily deciding component 1 is Z, component 2 is X
    if imu_data is not None:
        # For smoother control, tolerance considers total velocity, not components
        if value_within_tolerance(imu_vel):
            vel[2] = 0.0
            vel[0] = 0.0
        else:
            # Z component
            vel[2] = get_speed(imu_vel[0][0])
            # X component
            vel[0] = get_speed(imu_vel[1][0])
    return vel


def value_within_tolerance(velocity):
    value = np.sqrt(np.power(velocity[0][0],2) + np.power(velocity[1][0],2))*10
    if value > -TOLERANCE and value < TOLERANCE:
        return True
    return False


def get_speed(value):
    speed = np.min([abs(value)*10 - TOLERANCE, MAX_SPEED])
    return np.sign(value) * speed
