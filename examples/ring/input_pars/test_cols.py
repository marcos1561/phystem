import matplotlib.pyplot as plt
from pathlib import Path

from phystem.systems.ring.quantities.datas import CreationRateData, DensityVelData, DeltaData

def cr(path):
    data = CreationRateData(path / "cr")

    plt.title("num_created")
    plt.plot(data.time, data.num_created)

    plt.figure()

    plt.title("num_active")
    plt.plot(data.time, data.num_active)

    plt.show()

def den_vel(path):
    data = DensityVelData(path / "den_vel")

    plt.title("den")
    plt.plot(data.den_time, data.den, ".-")
    plt.figure()
    plt.title("vel")
    plt.plot(data.vel_time, data.vel, ".-")
    plt.show()

path = Path("datas/all")
# cr(path)
den_vel(path)
