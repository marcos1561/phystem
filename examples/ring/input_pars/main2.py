from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, RealTimeCfg, CollectDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graphs_cfg import SimpleGraphCfg

import pipeline

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    k_area=1,
    k_format=0.03*1,
    p0=3.5449077018*1, # Círculo
    p0_format=3.5449077018*1.0, # Círculo

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 12,
    adh_force = 1,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0,
    rot_diff=1,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 15,
    r = None, angle = [], center = [],
)

from math import cos, pi, ceil
radius = dynamic_cfg.diameter / (2 * (1 - cos(2*pi/(creator_cfg.num_p))))**.5

space_cfg = SpaceCfg(
    height = 6*radius*2,
    length = 20*radius*2,
)

stokes_cfg = StokesCfg(
    obstacle_r  = 2*radius,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 3,
    obs_force=15,
    num_max_rings = 100, 
)

seed = 40028922
# seed = None

##
## Select Run Type
##
run_type = RunType.REAL_TIME


num_cols = int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6)
num_rows = int(ceil(space_cfg.height/(dynamic_cfg.diameter*1.2)) * 0.6)

num_cols_cm = int(ceil(space_cfg.length / (2.5*radius)))
num_rows_cm = int(ceil(space_cfg.height / (2.5*radius)))

start_x = -5 * 2*radius
xlims = (start_x, start_x + 2*radius)

tf = 300
collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
            dt = 0.01,
            particle_win_cfg=ParticleWindows(
                num_cols=num_cols, num_rows=num_rows,
                update_freq=1),
            integration_type=IntegrationType.euler,
            update_type=UpdateType.STOKES,
            in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    ), 
    tf=tf,
    folder_path="data/teste",
    func=pipeline.collect_pipeline,
    func_cfg={
        "autosave_dt": 20,
        "den_vel": {
            "xlims": xlims,
            "vel_dt": 1,
            "den_dt": 1,
        },
        "delta": {
            "delta_wait_time": radius*2 * 2,
            "delta_wait_dist": radius*2 * 1,
            "xlims": xlims,
            "edge_k": 1.4,
            "debug": False,
        },
        "creation_rate": {
            "wait_time": 0,
            "collect_time": tf,
            "collect_dt": 1,
        },
    }, 
    #checkpoint=CheckpointCfg(
    #    folder_path="../creation_rate/data/init_state_low_flux_force/checkpoint"
    #    folder_path="data/low_adh_align_flux/autosave"
    #)
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    fps=30,
    num_steps_frame=10,
    graph_cfg=SimpleGraphCfg()
)

#collect_data_cfg.checkpoint.configs["dynamic_cfg"] = dynamic_cfg

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=real_time_cfg, other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)

sim.run()