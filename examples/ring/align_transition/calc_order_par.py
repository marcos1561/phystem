import os, sys, copy
from pathlib import Path
import numpy as np

from phystem.systems.ring import Simulation
from phystem.systems.ring.collectors import ColManager, DenVelCol, ColAutoSaveCfg, DeltaCol
from phystem.systems.ring.configs import SpaceCfg, RingCfg, CreatorCfg, RectangularGridCfg, StokesCfg
from phystem.systems.ring.ui.graph import graphs_cfg
from phystem.systems.ring.run_config import CollectDataCfg, CheckpointCfg, RealTimeCfg
from phystem.systems.ring import run_config, utils
from phystem.systems.ring.ui.graph import graphs_cfg
from phystem.utils import progress

sys.path.append(os.path.abspath('../extreme_pars'))
from extreme_pars import extreme_configs

def get_configs_align(num_rings_x, align, den, force):
    '''
    Retorna a configuração de integração e as configurações da simulação
    para o alinhamento.
    '''
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

def get_configs_delta(align, den, force):
    dynamic_cfg, stokes_cfg = extreme_configs.get(align=align, den=den, force=force)

    configs = {"dynamic_cfg": dynamic_cfg}
    
    configs["creator_cfg"] = CreatorCfg(
        num_rings = 0,
        num_particles = 10,
        r = None, angle = [], center = [],
    )   

    ring_r = utils.get_ring_radius(
        p_diameter=configs["dynamic_cfg"].diameter,
        num_particles=configs["creator_cfg"].num_particles
    )        

    space_scale = 0.2
    space_cfg = SpaceCfg(
        height=space_scale * 50 * 2 * ring_r,
        length=0.7 * space_scale * 200 * 2 * ring_r,
    )
    configs["space_cfg"] = space_cfg

    configs["other_cfgs"] = {
        "stokes": StokesCfg(
            obstacle_r=1,
            obstacle_x=0,
            obstacle_y=100000000,
            create_length=ring_r * 2.01,
            remove_length=ring_r * 2.01,
            flux_force=stokes_cfg["flux_force"],
            obs_force=1,
            num_max_rings=int(space_cfg.max_num_inside(2*ring_r)*1.05),
        )
    }

    num_cols, num_rows = space_cfg.particle_grid_shape(configs["dynamic_cfg"].max_dist)
    num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(ring_r)

    int_cfg=run_config.IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=run_config.ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=run_config.IntegrationType.euler,
        update_type=run_config.UpdateType.STOKES,
        in_pol_checker=run_config.InPolCheckerCfg(num_cols_cm, num_rows_cm, 100, 4),
    ) 

    return int_cfg, configs

def add_rot_diff_values(num_rings_x, align, den, force):
    int_cfg, configs = get_configs_align(
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


def run_sim(root_path: Path, tf, configs, int_cfg, col_name, ColT, col_cfg,
    rot_diff_range, ids):
    '''
    Roda uma simulação até o tempo `tf` para cada valor de ruído em `rot_diff_range`
    aplicando o coletar `ColT`. Para o i-ésimo ruído, a simulação é guardada na pasta
    `root_path/ids[i]`.
    * `configs` deve conter todas as configurações da simulação, menos a `run_cfg`.
    * Caso exista auto-salvamento para alguma simulação, ele será utilizado.
    '''
    for idx, rot_diff in zip(ids, rot_diff_range):
        data_path = root_path / f"{idx}"
        
        cp_path = data_path / "autosave"
        checkpoint = None
        if cp_path.exists():
            checkpoint = CheckpointCfg(cp_path)

        collect_cfg = CollectDataCfg(
            int_cfg=int_cfg,
            tf=tf,
            folder_path=data_path,
            func=ColManager.get_pipeline(cols={
                col_name: ColT,
            }),
            func_cfg={
                col_name: col_cfg, 
                "autosave_cfg": ColAutoSaveCfg(
                    freq_dt=50, save_data_freq_dt=50,
                ),
            },
            checkpoint=checkpoint,
        )

        configs["run_cfg"] = collect_cfg
        configs["dynamic_cfg"].rot_diff = rot_diff
        
        configs_cp = copy.deepcopy(configs)
        sim = Simulation(**configs_cp)
        sim.run()
    
    np.save(root_path / f"rot_diff_range.npy", rot_diff_range)

def find_transition_align(name, num_rings_x, rot_diff_range, tf, align, den, force):
    "Roda as simulações para todos os valores de ruído em `rot_diff_range` medindo o alinhamento."
    int_cfg, configs = get_configs_align(
        num_rings_x=num_rings_x,
        align=align, den=den, force=force,
    )
    configs["rng_seed"] = 356137951638
    
    length = configs["space_cfg"].length
    col_cfg = {
        "xlims": (-length, length),
        "vel_dt": 2,
        "density_dt": 100000000,
        "vel_frame_dt": int_cfg.dt * 10,
        "transient_time": 0,
    }

    root_path = Path("data") / f"{name}/{align}{den}{force}"
    run_sim(
        root_path=root_path, rf=tf, configs=configs, int_cfg=int_cfg, 
        col_name="den_vel", ColT=DenVelCol, col_cfg=col_cfg,
        rot_diff_range=rot_diff_range, ids=range(rot_diff_range.size),
    )

def find_transition_delta(name, rot_diff_range, tf, align, den, force):
    "Roda as simulações para todos os valores de ruído em `rot_diff_range` medindo o delta."
    int_cfg, configs = get_configs_delta(
        align=align, den=den, force=force,
    )
    configs["rng_seed"] = 356137951638
    
    length = configs["space_cfg"].length
    height = configs["space_cfg"].height
    ring_d = 2 * utils.get_ring_radius(
        p_diameter=configs["dynamic_cfg"].diameter,
        num_particles=configs["creator_cfg"].num_particles
    ) 
    vo = configs["dynamic_cfg"].vo

    wait_dist =  8 * ring_d
    col_cfg = {
        "wait_dist": 8 * ring_d,
        "xlims": [-ring_d, 0],
        "start_dt": ring_d/vo, 
        "check_dt":  wait_dist/8,
        "min_num_rings": int(height/ring_d * 0.8),
    }

    root_path = Path("data") / f"{name}/{align}{den}{force}"
    run_sim(
        root_path=root_path, tf=tf, configs=configs, int_cfg=int_cfg, 
        col_name="delta", ColT=DeltaCol, col_cfg=col_cfg,
        rot_diff_range=rot_diff_range, ids=range(rot_diff_range.size),
    )


def animate(int_cfg, configs):
    run_cfg = RealTimeCfg(
        int_cfg=int_cfg,
        num_steps_frame=10,
        graph_cfg=graphs_cfg.SimpleGraphCfg(
            begin_paused=True,
        ),
    )
    configs["run_cfg"] = run_cfg
    Simulation(**configs).run()

if __name__ == "__main__":
    configs = [
        (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 0, 0),
        (1, 0, 1), (1, 1, 0), (1, 1, 1), (1, 0, 0),
    ]
    
    config = configs[7]
    # config = configs[int(sys.argv[1])]

    # find_transition_extreme(
    #     name="delta_test",
    #     num_rings_x=10,
    #     tf=400,
    #     align=config[0], den=config[1], force=config[2],
    # )

    find_transition_delta(
        name="delta_test",
        rot_diff_range=np.linspace(0, 0.5, 3),
        tf=400,
        align=config[0], den=config[1], force=config[2],
    )
    
    # animate(*get_configs_align(
    #     num_rings_x=4,
    #     align=0, den=1, force=1
    # ))
    # animate(*get_configs_delta(
    #     align=0, den=1, force=1
    # ))