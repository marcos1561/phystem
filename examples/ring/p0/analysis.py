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

def den_dist(results_path, data_path, init_time, num_cols=5):
    data_path = Path(data_path)
    results_path = Path(results_path)

    p0_range = np.load(data_path / "p0_range.npy")
    
    from math import ceil
    num_rows =  ceil(p0_range.size / num_cols)
    
    fig, ax = plt.subplots(num_rows, num_cols) 
    
    den_results, _ = calculators.DenVelCalculator.load_data(results_path / '0/den_vel')

    ti = init_time
    tf = den_results.times[-1]

    fig.suptitle(f"$t \in [{round(ti, 2)}, {round(tf, 2)}]$")

    for idx, p_0 in enumerate(p0_range):
        den_results, _ = calculators.DenVelCalculator.load_data(results_path / str(idx) / 'den_vel')

        mask = den_results.times > init_time
        den = den_results.den_eq[mask]

        row_id = idx // num_cols
        col_id = idx % num_cols
        ax_i = ax[row_id, col_id]
        
        if row_id == num_rows - 1:
            ax_i.set_xlabel(r"$\delta_{eq}$")

        ax_i.hist(den, label=f"$p_0$ = {round(p_0, 3)}")
        ax_i.legend()
    plt.show()


def graph(i, data_path: Path, results_path):
    results_path = Path(results_path)
    data_path = Path(data_path)
    delta = calculators.DeltaCalculator.load_data(results_path / "delta")
    den, vel = calculators.DenVelCalculator.load_data(results_path / "den_vel")
    cr = datas.CreationRateData(data_path / "cr")
    
    fig, axs = plt.subplots(2, 3)
    fig.suptitle(i)

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



# graph(
#     data_path="../input_pars/datas/adh_1",
#     results_path="../input_pars/results/adh_1",
# )
# plt.show()

# data_name = "explore_p0_2000"
# p0_den("datas/" + data_name, "results/" + data_name, 
#     init_time=1000)
# plt.show()


data_name = "explore_p0_2000"
den_dist(
    results_path = "results/" + data_name,
    data_path = "datas/" + data_name,
    init_time=1000,
)

# for i in range(15):
#     data_name = "explore_p0_2000/" + str(i)

#     # crunch_numbers("datas/" + data_name, "results/" + data_name)
#     graph(i, "datas/" + data_name, "results/" + data_name)
#     # calc_den("results/" + data_name)

#     plt.show()