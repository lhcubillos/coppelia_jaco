import numpy as np
from sklearn.decomposition import PCA
import sys
import pickle as pk

data = np.genfromtxt("imucal",delimiter=",")
data_pca = PCA(n_components=2)
data_pca.fit(data)
f = open("imu_pca.pkl","wb")
pk.dump(data_pca, f)
f.close
