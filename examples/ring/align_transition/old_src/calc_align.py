import os, sys, copy
from pathlib import Path
import numpy as np

from phystem.systems.ring import Simulation
from phystem.systems.ring.collectors import ColManager, DenVelCol, ColAutoSaveCfg 
from phystem.systems.ring.configs import SpaceCfg, RingCfg, CreatorCfg, RectangularGridCfg
from phystem.systems.ring.run_config import CollectDataCfg, CheckpointCfg
from phystem.systems.ring import run_config
from phystem.systems.ring.ui.graph import graphs_cfg
from phystem.utils import progress

sys.path.append(os.path.abspath('../extreme_pars'))
from extreme_pars import extreme_configs

def get_configs(num_rings_x, align, den, force):
    dynamic_cfg, _ = extreme_configs.get(align=align, den=den, force=force)
    dynamic_cfg: RingCfg

    from math import pi
    import numpy as np
    from phystem.systems.ring import utils

    rel_den = {
        "000": -0.314,
        "100": -0.336,
        "010": -0.084,
        "001": -0.261,
        "110": 0.010,
        "101": -0.202,
        "011": -0.084,
        "111": -0.061,
    }

    '''
    A densidade de equilíbrio utilizada na coleta de dados foi 
        
        1/(área do anel considerando o raio até o centro da partícula)
    
    Já a densidade de equilíbrio utilizada pelo `RectangleGridCreator` é

        1/(área do quadrado que contém o anel, considerando o raio das partículas)

    Então é necessário fazer esse ajuste para obter a densidade de equilíbrio correta.
    '''
    radius = utils.get_ring_radius(dynamic_cfg.diameter, 10)
    real_diameter = 2 * utils.get_real_ring_radius(dynamic_cfg.diameter, 10)
    for key in list(rel_den.keys()):
        collect_d_eq = 1 / (np.pi * radius**2) 
        creator_d_eq = 1 / real_diameter**2 
        rel_den[key] = (rel_den[key] + 1) * collect_d_eq / creator_d_eq  - 1

    creator_cfg = RectangularGridCfg.from_relative_density(
        num_x=num_rings_x,
        num_y=num_rings_x,
        rel_density=rel_den[f"{align}{den}{force}"],
        num_particles=10,
        particle_diameter=dynamic_cfg.diameter,
        ring_radius_k = 0.7,
    )

    space_cfg = creator_cfg.get_space_cfg()

    radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles)
    num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
    num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(radius)
    int_cfg = run_config.IntegrationCfg(
        dt = 0.01,
        particle_win_cfg = run_config.ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1
        ),
        integration_type = run_config.IntegrationType.euler,
        update_type = run_config.UpdateType.PERIODIC_WINDOWS,
        in_pol_checker = run_config.InPolCheckerCfg(
            num_col_windows=num_cols_cm, num_rows_windows=num_rows_cm, 
            update_freq=200, steps_after=4
        ),
    )

    return int_cfg,  {"space_cfg": space_cfg, "creator_cfg": creator_cfg, "dynamic_cfg": dynamic_cfg}

def calc_align(sim: Simulation, cfg):
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg
    space_cfg: SpaceCfg = sim.configs["space_cfg"]

    length = space_cfg.length

    collectors = ColManager(
        solver=solver, root_path=collect_cfg.folder_path, configs=sim.configs,
        autosave_cfg=cfg["autosave_cfg"],
        to_load_autosave=collect_cfg.is_autosave,
    )

    den_vel_cfg = { 
        "xlims": (-length, length),
        "vel_dt": cfg["vel_dt"],
        "density_dt": 100000000,
        "vel_frame_dt": sim.run_cfg.int_cfg.dt * cfg["vel_dt_steps"],
        "transient_time": cfg["transient_time"],
    }

    collectors.add_collector(DenVelCol, den_vel_cfg, "den_vel")

    prog = progress.Continuos(collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        solver.update()
        collectors.collect()
        prog.update(solver.time)

    collectors.save()
    prog.update(solver.time)

def visual_inspect():
    num_rings_x = 10
    align, den, force = 1, 1, 0
    
    int_cfg, configs = get_configs(
        num_rings_x=num_rings_x,
        align=align, den=den, force=force,
    )

    real_time_cfg = run_config.RealTimeCfg(
        int_cfg=int_cfg,
        num_steps_frame = 20,
        fps = 30,
        graph_cfg = graphs_cfg.SimpleGraphCfg(
            begin_paused=True,
            show_scatter=False,
            show_circles=True,
            circle_facecolor=True,
            scatter_kwargs={"s": 1},
            density_kwargs={"vmin": -1, "vmax":1},
            cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
            ax_kwargs={"title": "Maior densidade"},
            cell_shape=[3, 3],
        ),
    )

    configs["run_cfg"] = real_time_cfg
    Simulation(**configs).run()


def add_rot_diff_values(num_rings_x, align, den, force):
    int_cfg, configs = get_configs(
        num_rings_x=num_rings_x,
        align=align, den=den, force=force,
    )

    root_path = Path(f"data/{align}{den}{force}")

    rot_diff_path = root_path / "rot_diff_range.npy"
    rot_diff_range = np.load(rot_diff_path) 
    next_id = rot_diff_range.size

    new_rot_diff_range = np.linspace(1, 2, 20)[1:]
    ids = range(next_id, next_id + new_rot_diff_range.size)
    
    run_sim(root_path, configs, int_cfg, new_rot_diff_range, ids)
    np.save(rot_diff_path, np.concatenate((rot_diff_range, new_rot_diff_range)))

def find_transition_extreme(num_rings_x, align, den, force):
    int_cfg, configs = get_configs(
        num_rings_x=num_rings_x,
        align=align, den=den, force=force,
    )
    configs["rng_seed"] = 356137951638

    root_path = Path("data") / f"{align}{den}{force}"
    
    rot_diff_range = np.linspace(0, 2, 40) 
    ids = range(rot_diff_range.size)
    
    rot_diff_path = root_path / f"root_diff_range.npy"
    np.save(rot_diff_path, rot_diff_range)
    
    run_sim(root_path, configs, int_cfg, rot_diff_range, ids)

    # for idx, rot_diff in enumerate(rot_diff_range):
    #     data_path = root_path / f"{idx}"
        
    #     cp_path = data_path / "autosave"
    #     checkpoint = None
    #     if cp_path.exists():
    #         checkpoint = CheckpointCfg(cp_path)

    #     collect_cfg = CollectDataCfg(
    #         int_cfg=int_cfg,
    #         tf=800,
    #         folder_path=data_path,
    #         func=calc_align,
    #         func_cfg={
    #             "vel_dt": 2,
    #             "vel_dt_steps": 10, 
    #             "transient_time": 0,
    #             "autosave_cfg": ColAutoSaveCfg(
    #                 freq_dt=50, save_data_freq_dt=50,
    #             ),
    #         },
    #         checkpoint=checkpoint,
    #     )

    #     configs["run_cfg"] = collect_cfg
    #     configs["dynamic_cfg"].rot_diff = rot_diff
    #     configs_cp = copy.deepcopy(configs)
    #     sim = Simulation(**configs_cp, rng_seed=rng_seed)
    #     sim.run()

def run_sim(root_path, configs, int_cfg, rot_diff_range, ids):
    for idx, rot_diff in zip(ids, rot_diff_range):
        data_path = root_path / f"{idx}"
        
        # cp_path = data_path / "autosave"
        # checkpoint = None
        # if cp_path.exists():
        #     checkpoint = CheckpointCfg(cp_path)

        collect_cfg = CollectDataCfg(
            int_cfg=int_cfg,
            tf=800,
            folder_path=data_path,
            func=calc_align,
            func_cfg={
                "vel_dt": 2,
                "vel_dt_steps": 10, 
                "transient_time": 0,
                "autosave_cfg": ColAutoSaveCfg(
                    freq_dt=50, save_data_freq_dt=50,
                ),
            },
        )

        configs["run_cfg"] = collect_cfg
        configs["dynamic_cfg"].rot_diff = rot_diff
        configs_cp = copy.deepcopy(configs)
        sim = Simulation(**configs_cp)
        sim.run()

if __name__ == "__main__":
    visual_inspect()

    # add_rot_diff_values(
    #     num_rings_x=10,
    #     align=1, den=1, force=0,
    # )

    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=1, den=1, force=0,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=0, den=0, force=0,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=0, den=1, force=0,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=0, den=0, force=1,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=1, den=1, force=0,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=1, den=0, force=1,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=0, den=1, force=1,
    # )
    # find_transition_extreme(
    #     num_rings_x=10,
    #     align=1, den=1, force=1,
    # )