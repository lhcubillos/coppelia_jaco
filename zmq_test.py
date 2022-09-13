import time
import sys
print(sys.path)
sys.path.insert(1,"/home/neurro/Desktop/jaco/CoppeliaSim_Edu_V4_3_0_Ubuntu20_04/programming/zmqRemoteApi/clients/python")
from zmqRemoteApi import RemoteAPIClient


###########################################################################
# Simple script to confirm that ZMQ is working correctly.
# IMPORTANT: Make the above your path to:
# CoppeliaSim/programming/zmqRemoteApi/clients/python
# If you do not, it will fail to import zmq for hooking CoppeliaSim!
# Can use the Viewer or Edu. Same filepath format as in jaco.py.
###########################################################################


client = RemoteAPIClient()
sim = client.getObject('sim')
client.setStepping(True)

sim.startSimulation()
while (t := sim.getSimulationTime()) < 3:
    s = f'Simulation time: {t:.2f} [s]'
    print(s)
    client.step()
sim.stopSimulation()
