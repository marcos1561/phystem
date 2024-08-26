import matplotlib.pyplot as plt
import matplotlib.axes as Axes
from pathlib import Path

from phystem.systems.ring.quantities import calculators, datas
from phystem.data_utils import utils as data_utils

def graph(results_paths):
    if type(results_paths) != list:
        results_paths = [results_paths]

    fig, axs = plt.subplots(2, 3)
    
    for results_path in results_paths:
        results_path = Path(results_path)
        delta = calculators.DeltaCalculator.load_data(results_path / "delta")
        den, vel = calculators.DenVelCalculator.load_data(results_path / "den_vel")
        cr = datas.CreationRateData(results_path / "cr")
        

        def delta_graph(ax: Axes):
            ax.set_title("Delta")
            ax.set_ylabel("$\Delta$")

            ax.plot(delta.times, delta.deltas, ".-")

        def den_graph(ax: Axes): 
            ax.set_title("Densidade")
            ax.set_ylabel("$\delta_{eq}$")

            k_den = 4
            ax.plot(
                data_utils.mean_arr(den.times, k_den), 
                data_utils.mean_arr(den.den_eq, k_den), 
            ".-")
        
        def vel_graph(ax: Axes):
            ax.set_title("V")
            ax.set_ylabel(r"$\langle V \rangle$")

            k_vel = 4
            ax.plot(
                data_utils.mean_arr(vel.times, k_vel), 
                data_utils.mean_arr(vel.vel_par, k_vel), 
                ".-",
            )
    
        def created_graph(ax: Axes):    
            ax.set_title("Taxa de criação instantânea")
            ax.set_ylabel("Taxa de criação (Nº criados / Un. de tempo)")    
            
            ax.set_xscale("log")    
            ax.set_yscale("log")    
            
            r = 1.1
            k_created = 20
            ax.plot(
                data_utils.mean_arr(cr.time, k_created, r=r), 
                data_utils.mean_arr(cr.num_created, k_created, r=r), 
                ".-",
            )
        
        def active_graph(ax: Axes):
            ax.set_title("Ativos")
            ax.set_ylabel("Nº de anéis ativos")

            ax.plot(cr.time, cr.num_active, ".-")

        delta_graph(axs[0, 0])
        den_graph(axs[0, 1])
        vel_graph(axs[0, 2])
        created_graph(axs[1, 0])
        active_graph(axs[1, 1])

    for ax in axs[1]:
        ax.set_xlabel("Tempo")

# graph("results/adh_1")
# graph("results/adh_1_2")
# graph("results/adh_1_7")
graph("results/test_save_data")
# graph([
#     "results/adh_1_3",
#     "results/adh_1_bigger_force",
# ])
plt.show()