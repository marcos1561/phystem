from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph import GraphCfg

import pipeline


dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    # area_potencial="target_area",
    k_area=2,
    k_format=0.1,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.0, # Círculo
    # area0=53,

    diameter  = 1,
    max_dist  = 1 + 0.1666,
    rep_force = 30,
    adh_force = 0.75,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)


space_cfg = SpaceCfg(
    height = 2*30,
    length = 2.5*30,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 30,
    r = None, angle = [], center = [],
)

from math import cos, pi, ceil
radius = dynamic_cfg.diameter / (2 * (1 - cos(2*pi/(creator_cfg.num_p))))**.5
stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/6,
    obstacle_x  = 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 2, 
    num_max_rings = 100, 
)

seed = 40028922
# seed = None


##
## Select Run Type
##
run_type = RunType.SAVE_VIDEO


num_cols = int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6)
num_rows = int(ceil(space_cfg.height/(dynamic_cfg.diameter*1.2)) * 0.6)

num_cols_cm = int(ceil(space_cfg.length / (2.5*radius)))
num_rows_cm = int(ceil(space_cfg.height / (2.5*radius)))

collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
            dt = 0.01,
            particle_win_cfg=ParticleWindows(
                num_cols=num_cols, num_rows=num_rows,
                update_freq=1),
            integration_type=IntegrationType.euler,
            update_type=UpdateType.PERIODIC_WINDOWS,
            in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    ), 
    tf = 20,
    func=pipeline.collect_pipeline,
    folder_path="data",
    func_cfg=pipeline.PipelineCfg(
        save_time_freq=2),
    checkpoint=CheckpointCfg(
        folder_path="data",
        override_cfgs=False,
    )
)

real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001*10, # max euler
        # dt = 0.001*5 * 1.55,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50, disable=False),
    ),
    num_steps_frame=1200,
    fps=60,
    graph_cfg = GraphCfg(
        show_circles      = True,
        show_f_spring     = False,
        show_f_vol        = False,
        show_f_area       = False,
        show_f_total      = False,
        show_center_mass  = True,
        show_inside       = True,
        begin_paused      = False,
        pause_on_high_vel = True,
        cpp_is_debug      = True
    ),
    # checkpoint=CheckpointCfg(
    #     folder_path="data",
    #     override_cfgs=False,
    # )
)

video_cfg = SaveCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001*10, # max euler
        # dt = 0.001*5 * 1.55,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50, disable=False),
    ),
    path="./video_teste2.mp4",
    speed=5,
    duration=10,
    fps=30,
    graph_cfg = GraphCfg(
        show_circles      = True,
        show_f_spring     = False,
        show_f_vol        = False,
        show_f_area       = False,
        show_f_total      = False,
        show_center_mass  = True,
        show_inside       = False,
    ),
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: video_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type],
    other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)

sim.run()
