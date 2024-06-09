import numpy as np

from phystem.systems.ring.quantities.calculators import DenVelCalculator,  DeltaCalculator, CalcAutoSaveCfg
from phystem.systems.ring.quantities.datas import CreationRateData

from pathlib import Path


def graph_results(root_path):
    root_path = Path(root_path)
    cr_data = CreationRateData(root_path / "cr")
    delta = DeltaCalculator(root_path / "delta", edge_k=1.7, root_path="results/delta")
    den_vel = DenVelCalculator(root_path / "den_vel", root_path="results/den_vel")

    delta.crunch_numbers(to_save=True)
    den_vel.crunch_numbers(to_save=True)

    import matplotlib.pyplot as plt

    plt.subplot(231)
    plt.title("Num Created")
    plt.plot(cr_data.time, cr_data.num_created, ".-")
    plt.subplot(232)
    plt.title("Num Active")
    plt.plot(cr_data.time, cr_data.num_active, ".-")

    plt.subplot(233)
    plt.title("Delta")
    plt.plot(delta.times, delta.deltas, ".-")

    plt.subplot(234)
    plt.title("Den")
    plt.plot(den_vel.data.den_time, den_vel.den_eq, ".-")
    plt.subplot(235)
    plt.title("Vel")
    plt.plot(den_vel.data.vel_time, den_vel.vel_order_par, ".-")

    plt.show()

def test_autosave(data_path): 
    calc = DeltaCalculator(data_path, edge_k=1.7, root_path="results/test_autosave1")
    calc.crunch_numbers()

    calc2 = DeltaCalculator(data_path, edge_k=1.7, root_path="results/test_autosave2",
        autosave_cfg=CalcAutoSaveCfg(freq=3))
    calc2.crunch_numbers(id_stop=7)

    calc2 = DeltaCalculator.from_checkpoint("results/test_autosave2/autosave")
    calc2.crunch_numbers()

    print("deltas diff:", ((np.array(calc.deltas) - np.array(calc2.deltas))**2).sum())
    print("times diff :", ((np.array(calc.times) - np.array(calc2.times))**2).sum())

# test_autosave("datas/all/delta")
graph_results("datas/all")