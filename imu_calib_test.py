import time
import numpy as np
from zerocm import ZCM
from sklearn.decomposition import PCA
import sys
import pickle as pk
import tkinter as tk
import subprocess

from zcmtypes.imus_t import imus_t
from zcmtypes.euler_t import euler_t

from collections import deque

# Simple script that prints some relevant values from a .calib file

class CalibrateImu:
    def __init__(self,):
        self.filename = "test"
        self.first_time = None
        self.f = None
        
    def runCalib(self,filename):
        data = np.genfromtxt(filename,delimiter=",")
        data_pca = PCA(n_components=2)
        data_pca.fit(data)
        pca_transform=data_pca.transform(np.identity(8))
        norms = np.linalg.norm(pca_transform,2,0)
        eigen = data_pca.singular_values_
        variances = data_pca.explained_variance_
        print(variances)
        print(eigen)
        [n,m] = np.shape(pca_transform)
        pca_normalized = pca_transform
        for i in range(n):
            for j in range(m):
                pca_normalized[i,j] = (pca_transform[i,j]/norms[j])/np.sqrt(variances[j])
        print(pca_normalized)

if __name__ == "__main__":
    filename = sys.argv[1]
    print(filename)
    calibrate = CalibrateImu()
    calibrate.runCalib(filename)

