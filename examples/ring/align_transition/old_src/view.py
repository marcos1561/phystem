import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from pathlib import Path
import numpy as np
import pickle

from phystem.systems.ring.quantities import datas
from phystem.systems.ring.quantities import calculators

def align_curve_data(time_cut, align, den, force):
    noise = []
    vel_order_par = []
    vel_order_par_std = []

    extreme_name = f"{align}{den}{force}"
    data_path = Path(f"data/{extreme_name}")
    
    noise_range = np.load(data_path / "rot_diff_range.npy")

    for path in data_path.glob("[0-9]*"):
        den_vel_data = datas.DenVelData(path / "den_vel")

        result_path = Path("results")
        for part_i in path.parts[1:]:
            result_path /= part_i
        den_vel_calc = calculators.DenVelCalculator(den_vel_data, result_path)
        den_vel_calc.crunch_numbers(to_save=False)

        mask = den_vel_data.vel_time > time_cut

        vel_order_par.append(den_vel_calc.vel_order_par[mask].mean())
        vel_order_par_std.append(den_vel_calc.vel_order_par[mask].std())
        noise.append(noise_range[int(path.parts[-1])])
    
    return noise, vel_order_par, vel_order_par_std

def calc_align_curves():
    root_path = Path("data")
    time_cut = 400

    curves = {}
    for data_path in root_path.iterdir():
        name = data_path.parts[-1]
        align, den, force = [int(i) for i in name]
        
        noise, vel_mean, vel_std = align_curve_data(time_cut, align, den, force)
        curves[name] = {
            "noise": noise,
            "vel_mean": vel_mean,
            "vel_std": vel_std,
        }

    with open("results/align_curves.pickle", "wb") as f:
        pickle.dump(curves, f)

def view_align_curves(paths, labels=None):
    if type(paths) != list:
        paths = [paths]
    
    if type(labels) != list:
        labels = [labels]

    fig, axs = plt.subplots(2, 4)
    
    for path, label in zip(paths, labels):
        with open(Path(path) / "align_curves.pickle", "rb") as f:
            curves = pickle.load(f) 

        row_configs = [(0, 0), (1, 0), (0, 1), (1, 1)]
        
        for row_id in range(2):
            for col_id, config in enumerate(row_configs):
                curve = curves[f"{row_id}{config[0]}{config[1]}"] 

                ax: Axes = axs[row_id, col_id]

                label_i = None
                if row_id == 0 and col_id == 0:
                    label_i = label

                ax.errorbar(curve["noise"], curve["vel_mean"], curve["vel_std"], fmt=".", label=label_i)

    for row_id in range(axs.shape[0]):
        for col_id in range(axs.shape[1]):
            ax = axs[row_id, col_id]
        
            label = None
            if row_id == 0 and col_id == 0:
                label = "Ruído utilizado\nno fluxo de Stokes"   

            ax.plot([1/3, 1/3], [0, 1], c="black", label=label)
            ax.set_title(f"A{row_id}-D{config[0]}-F{config[1]}")

    axs[0, 0].legend()
    fig.supxlabel("$D_r$ (Ruído rotacional)")
    fig.supylabel("$\phi$ (Alinhamento)")

    plt.show()

if __name__ == "__main__":
    # calc_align_curves()
    view_align_curves(
        paths = ["results/bigger/results", "results"], 
        labels=["400 anéis", "100 anéis"]
    )