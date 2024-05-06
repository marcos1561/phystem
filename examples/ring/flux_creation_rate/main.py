import numpy as np

from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graphs_cfg import *
from phystem.systems.ring import utils

import pipeline

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    # area_potencial="target_area",
    k_area=2,
    k_format=0.03,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.0, # Círculo
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 12,
    adh_force = 0.5,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0,
    rot_diff=0.5,
)

space_cfg = SpaceCfg(
    height = 2*30,
    length = 4*30,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 15,
    r = None, angle = [], center = [],
)

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p) 
stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 5, 
    obs_force = 15,
    num_max_rings = 400, 
)

##
## Select Run Type
##
run_type = RunType.COLLECT_DATA


num_cols, num_rows = utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = utils.rings_grid_shape(space_cfg, radius)

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
    tf=-1,
    folder_path="data/test2",
    func=pipeline.collect_pipeline,
    func_cfg={
        "wait_time": 30,
        "collect_time": 30,
        "collect_dt": 1,
        "autosave_dt": 5,
        # "flux_range": np.linspace(0.1),
        "flux_range": [0.1],
    },
    # checkpoint=CheckpointCfg("data/test/autosave")
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=1,
    fps=30,
    graph_cfg = SimpleGraphCfg(begin_paused=True),
    # graph_cfg = MainGraphCfg(
    #     show_circles      = True,
    #     show_f_spring     = False,
    #     show_f_vol        = False,
    #     show_f_area       = False,
    #     show_f_total      = False,
    #     show_center_mass  = False,
    #     show_inside       = False,
    #     begin_paused      = True,
    #     pause_on_high_vel = True,
    #     cpp_is_debug      = True
    # ),
)

video_cfg = SaveCfg(
    int_cfg = collect_data_cfg.int_cfg,
    path="./color_test.mp4",
    tf=200,
    # speed=5,
    duration=10,
    fps=30,
    graph_cfg = MainGraphCfg(
        show_circles      = True,
        show_f_spring     = False,
        show_f_vol        = False,
        show_f_area       = False,
        show_f_total      = False,
        show_center_mass  = True,
        show_inside       = False,
        cpp_is_debug      = False,
    ),
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: video_cfg,
}

configs = {
    "creator_cfg": creator_cfg, "dynamic_cfg": dynamic_cfg, 
    "space_cfg": space_cfg, "run_cfg": run_type_to_cfg[run_type],
    "other_cfgs": {"stokes": stokes_cfg}
}

if run_type is RunType.COLLECT_DATA:
    pipeline.main(configs, rng_seed=996925520)
else:
    sim = Simulation(**configs)
    sim.run()