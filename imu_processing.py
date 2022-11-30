import numpy as np
from sklearn.decomposition import PCA
import pickle as pk

###########################################################################
# This script contains the functions used to process IMU inputs via PCA.
# Any function that calculates velocities should be contained herein.
###########################################################################

# These values are based on a combination of observation
# and the specifications of the jaco arm, and are in meters per second.
MAX_SPEED = 0.2

# Compute velocity from an IMU input and a PCA matrix
def compute_velocity(imu_data,pca,vel_tolerance):
    imu_data_1 = imu_data[:, 0:4]
    pca_1 = pca[:, 0:2]
    imu_data_2 = imu_data[:, 4:8]
    pca_2 = pca[:, 2]
    imu_vel_1 = np.matmul(pca_1.T,imu_data_1.T)
    imu_vel_2 = np.matmul(pca_2.T,imu_data_2.T)
    vel = [0.0, 0.0, 0.0]
    # Arbitratily deciding component 1 is Z, component 2 is X
    if imu_data is not None:
        # Z component
        vel[1] = get_speed(imu_vel_2[0], vel_tolerance)
        if (abs(imu_vel_1[1][0]) > abs(imu_vel_1[0][0])):
            # Y component
            vel[2] = get_speed(imu_vel_1[1][0], vel_tolerance)
            vel[0] = 0.0
        else:
            # X component
            vel[0] = get_speed(imu_vel_1[0][0], vel_tolerance)
            vel[2] = 0.0
        # For smoother control, tolerance considers total velocity, not components
        if value_within_tolerance(vel, vel_tolerance):
            vel[2] = 0.0
            vel[1] = 0.0
            vel[0] = 0.0
    return vel

# Check if calculated velocity is within the "deadzone" tolerance; if so,
# instructs the processing to return zero velocity
def value_within_tolerance(velocity, vel_tolerance):
    value = np.sqrt(np.power(velocity[0]+vel_tolerance,2) + np.power(velocity[1]+vel_tolerance,2) + np.power(velocity[2]+vel_tolerance,2))
    if value<vel_tolerance:
        return True
    return False

# Simple function to calculate the speed and sign of a velocity component,
# and limits the result to be at most MAX_SPEED
def get_speed(value, vel_tolerance):
    speed = np.min([np.max([abs(value) - vel_tolerance,0]), MAX_SPEED])
    return np.sign(value) * speed

