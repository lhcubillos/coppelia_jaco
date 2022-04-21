import time
import sys
print(sys.path)
sys.path.insert(1,"/home/xander/coppelia/coppelia_jaco/CoppeliaSim_Edu_V4_3_0_Ubuntu20_04/programming/zmqRemoteApi/clients/python")
from zmqRemoteApi import RemoteAPIClient
client = RemoteAPIClient()
sim = client.getObject('sim')
client.setStepping(True)

sim.startSimulation()
while (t := sim.getSimulationTime()) < 3:
    s = f'Simulation time: {t:.2f} [s]'
    print(s)
    client.step()
sim.stopSimulation()
