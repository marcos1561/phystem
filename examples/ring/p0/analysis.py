import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from phystem.systems.ring.quantities import calculators, datas
from phystem.data_utils import utils
from pathlib import Path

def crunch_numbers(data_path: Path, root_path):
    data_path = Path(data_path)
    root_path = Path(root_path)
    calculators.DeltaCalculator(data_path / "delta", 
        edge_k=1.3, root_path=root_path/"delta", debug=True,
    ).crunch_numbers(to_save=True)
    
    calculators.DenVelCalculator(data_path / "den_vel", 
        root_path=root_path/"den_vel"
    ).crunch_numbers(to_save=True)

def calc_den(results_path, init_time):
    results_path = Path(results_path)
    den_results, _ = calculators.DenVelCalculator.load_data(results_path / 'den_vel')

    mask = den_results.times > init_time
    den = den_results.den_eq[mask]

    mean, std = den.mean(), den.std()
    
    return mean, std

def graph(data_path: Path, results_path):
    results_path = Path(results_path)
    data_path = Path(data_path)
    delta = calculators.DeltaCalculator.load_data(results_path / "delta")
    den, vel = calculators.DenVelCalculator.load_data(results_path / "den_vel")
    cr = datas.CreationRateData(data_path / "cr")
    
    fig, axs = plt.subplots(2, 3)

    def delta_graph(ax: Axes):
        ax.set_title("Delta")
        ax.set_ylabel("$\Delta$")

        ax.plot(delta.times, delta.deltas, ".-")

    def den_graph(ax: Axes): 
        ax.set_title("Densidade")
        ax.set_ylabel("$\delta_{eq}$")

        k_den = 4
        ax.plot(
            utils.mean_arr(den.times, k_den), 
            utils.mean_arr(den.den_eq, k_den), 
        ".-")
    
    def vel_graph(ax: Axes):
        ax.set_title("V")
        ax.set_ylabel(r"$\langle V \rangle$")

        k_vel = 4
        ax.plot(
            utils.mean_arr(vel.times, k_vel), 
            utils.mean_arr(vel.vel_par, k_vel), 
            ".-",
        )
    
    def created_graph(ax: Axes):    
        ax.set_title("Criados")
        ax.set_ylabel("N° de anéis criados")    
        
        # ax.set_xscale("log")    
        # ax.set_yscale("log")    
        
        r = 1.1
        k_created = 4
        ax.plot(
            utils.mean_arr(cr.time, k_created, r=r), 
            utils.mean_arr(cr.num_created, k_created, r=r), 
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

def p0_den(data_path, results_path, init_time):
    data_path = Path(data_path)
    results_path = Path(results_path)

    p0_range = np.load(data_path / "p0_range.npy")
    # p0_range = p0_range[:6]

    den_measures = {"mean": [], "std": []}
    for idx in range(p0_range.size):
        den_mean, den_std = calc_den(results_path / str(idx), init_time=init_time)
        den_measures["mean"].append(den_mean)
        den_measures["std"].append(den_std)

    plt.xlabel("$p_0$")
    plt.ylabel("$\delta_{eq}$")
    plt.errorbar(p0_range, den_measures["mean"], den_measures["std"], ecolor="black", capsize=2, fmt="o")


data_name = "explore_p0"
p0_den("datas/" + data_name, "results/" + data_name, 
    init_time=650)
plt.show()

# for i in range(15):
#     data_name = "explore_p0/" + str(i)

#     crunch_numbers("datas/" + data_name, "results/" + data_name)
#     graph("datas/" + data_name, "results/" + data_name)
#     # calc_den("results/" + data_name)

#     plt.show()