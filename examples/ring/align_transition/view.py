import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from pathlib import Path
import numpy as np
import pickle

from phystem.systems.ring.quantities import datas
from phystem.systems.ring.quantities import calculators

def transition_curve_data(name, data_folder_name, DataT: type[datas.BaseData], CalcT: type[calculators.Calculator], 
    time_cut, align, den, force, calc_kwargs={}, save_calc_data=False):
    '''
    Calcula e retorna o valor do parâmetro de ordem, para `t>time_cut`, em cada simulação no
    caminho `datas/name`.
    '''
    noise = []
    vel_order_par = []
    vel_order_par_std = []

    extreme_name = f"{align}{den}{force}"
    data_path = Path(f"data/{name}/{extreme_name}")
    
    noise_range = np.load(data_path / "rot_diff_range.npy")

    for path in data_path.glob("[0-9]*"):
        data = DataT(path / data_folder_name)

        result_path = Path(f"results/{name}")
        for part_i in path.parts[1:]:
            result_path /= part_i
        calc = CalcT(data=data, root_path=result_path, **calc_kwargs)
        calc.crunch_numbers(to_save=save_calc_data)

        time, order_par = get_order_par_values(data, calc)

        mask = time > time_cut

        vel_order_par.append(order_par[mask].mean())
        vel_order_par_std.append(order_par[mask].std())
        noise.append(noise_range[int(path.parts[-1])])
    
    return noise, vel_order_par, vel_order_par_std

def get_order_par_values(data, calc):
    '''
    Retorna o tempo e o valor do parâmetro de ordem para o respectivo tempo,
    dados os dados e o calculador do mesmo.
    '''
    if type(data) == datas.DeltaData:
        func = get_delta_par_values
    elif type(data) == datas.DenVelData:
        func = get_align_par_values
    return func(data, calc)

def get_align_par_values(data: datas.DenVelData, calc: calculators.DenVelCalculator):
    return data.vel_time, calc.vel_order_par

def get_delta_par_values(data: datas.DeltaData, calc: calculators.DeltaCalculator):
    "Retorna o tempo e o valor do parâmetro de ordem para o respectivo tempo"
    return data.final_times, calc.deltas

def calc_order_par_curves(root_name, time_cut, data_folder_name, DataT, CalcT, 
    calc_kwargs={}, save_calc_data=False):
    '''
    Calcula as curvas do parâmetro de ordem em função do ruído para todos os casos
    no caminho `data/root_name`.
    '''
    root_path = Path(f"data/{root_name}")

    curves = {}
    for data_path in root_path.iterdir():
        config_id = data_path.parts[-1]
        if len(config_id) != 3:
            continue

        align, den, force = [int(i) for i in config_id]

        noise, vel_mean, vel_std = transition_curve_data(
            name=root_name, data_folder_name=data_folder_name, 
            DataT=DataT, CalcT=CalcT,
            time_cut=time_cut,
            calc_kwargs=calc_kwargs,
            save_calc_data=save_calc_data,
            align=align, den=den, force=force)
        curves[config_id] = {
            "noise": noise,
            "vel_mean": vel_mean,
            "vel_std": vel_std,
        }

    with open(f"results/{root_name}/align_curves.pickle", "wb") as f:
        pickle.dump(curves, f)


def view_order_par_curves(paths, labels, xlabel, ylabel):
    '''
    Gráfico da curvas do parâmetro de ordem em função do ruído para todos
    os casos. Se `paths` é uma lista, sobrepõem os dados identificando os
    mesmo com as labels em `labels`.
    '''
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
                curve = curves.get(f"{row_id}{config[0]}{config[1]}")
                if curve is None:
                    continue

                ax: Axes = axs[row_id, col_id]

                label_i = None
                if row_id == 0 and col_id == 0:
                    label_i = label

                ax.errorbar(curve["noise"], curve["vel_mean"], curve["vel_std"], fmt=".", label=label_i)
                ax.set_title(f"A{row_id}-D{config[0]}-F{config[1]}")

    for row_id in range(axs.shape[0]):
        for col_id in range(axs.shape[1]):
            ax = axs[row_id, col_id]
        
            label = None
            if row_id == 0 and col_id == 0:
                label = "Ruído utilizado\nno fluxo de Stokes"   

            ax.plot([1/3, 1/3], [0, 1], c="black", label=label)

    axs[0, 0].legend()
    fig.supxlabel(xlabel)
    fig.supylabel(ylabel)

    plt.show()
 
def view_align_curves(paths, labels=None):
    view_order_par_curves(paths, labels,
        xlabel="$D_r$ (Ruído rotacional)",
        ylabel="$\phi$ (Alinhamento)",
    )

def view_delta_curves(paths, labels=None):
    view_order_par_curves(paths, labels,
        xlabel="$D_r$ (Ruído rotacional)",
        ylabel="$\Delta$ (Sólido/Líquido)",
    )

def graph_align_result(path, to_show=True):
    _, results = calculators.DenVelCalculator.load_data(path)

    plt.xlabel("Tempo")
    plt.xlabel("$\phi$ (Alinhamento)")

    plt.plot(results.times, results.vel_par)

    if to_show:
        plt.show()

def graph_all_align_results(path, data_path, num_cols, num_rows):
    '''
    Faz os gráficos do parâmetro de ordem em função do tempo
    para `num_cols * num_rows` gráficos com o ruído espaçado entre
    os gráficos nos dados em `path`.
    '''
    path = Path(path)

    def sort_relative(a, b):
        return [x for _, x in sorted(zip(b, a))]

    case_code = path.parts[-1]

    rot_diff_range = np.load(Path(data_path) / f"{case_code}/rot_diff_range.npy")
    ids = []    
    paths = []
    for path_i in path.iterdir():
        ids.append(int(path_i.parts[-1]))
        paths.append(path_i)
    
    paths = sort_relative(paths, ids)
    ids.sort()

    num_graphs = num_cols * num_rows

    step = int((len(ids)-1) / (num_graphs-1))

    while int((len(ids) - 1) / step) + 1 > num_graphs:
        step += 1

    fig, axs = plt.subplots(num_rows, num_cols)

    indices = [int(i) for i in np.linspace(0, len(ids)-1, num_graphs)]
    for count, i in enumerate(indices):
        col_id = count % num_cols
        row_id = count // num_cols
        ax = axs[row_id, col_id]
        ax: Axes
         
        print(paths[i])
        _, results = calculators.DenVelCalculator.load_data(paths[i])

        ax.plot(results.times, results.vel_par)
        ax.set_title(f"$D_r$ = {rot_diff_range[ids[i]]:.3f}")

    title = f"A{case_code[0]}-D{case_code[1]}-F{case_code[2]}"

    fig.supxlabel("Tempo")
    fig.supylabel("$\phi$ (Alinhamento)")
    fig.suptitle(title)

    plt.show()


if __name__ == "__main__":
    # calc_order_par_curves(
    #     root_name="delta_test",
    #     time_cut=10,
    #     data_folder_name="delta",
    #     DataT=datas.DeltaData, CalcT=calculators.DeltaCalculator,
    #     calc_kwargs={"edge_k": 1.4},
    # )

    # calc_order_par_curves(
    #     root_name="align",
    #     time_cut=300,
    #     data_folder_name="den_vel",
    #     save_calc_data=True,
    #     DataT=datas.DenVelData, CalcT=calculators.DenVelCalculator,
    # )

    # view_delta_curves(
    #     paths="results/delta_test",
    # )
    
    view_align_curves(
        paths="results/align",
    )
    # view_align_curves(
    #     paths=["results/align_bigger", "results/align"],
    #     labels=["400 anéis", "100 anéis"],
    # )

    # graph_align_result("results/align/align/100/19")
    graph_all_align_results("results/align/align/100", "data/align/", 2, 3)

