from math import ceil

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring import collect_pipelines

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph import GraphCfg


dynamic_cfg = RingCfg(
    spring_k=10,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=4,
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


from math import pi
radius = 20/6 * 1.1
a = 2
creator_cfg = CreatorCfg(
    num_rings = 4,
    num_p = 30,
    r = radius,
    angle=[pi/4, 0, 0, 0],
    center=[
        [-a * radius, -a * radius], 
        [a * radius, a * radius], 
        [a * radius, -a * radius], 
        [-a * radius, a * radius], 
    ]
)

stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/6,
    obstacle_x  = 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 3,
    remove_length = radius * 3,
    flux_force = 0.5, 
    num_max_rings = 100, 
)

seed = 40028922
seed = None

run_type = RunType.REAL_TIME

num_cols = int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6)
num_rows = int(ceil(space_cfg.height/(dynamic_cfg.diameter*1.2)) * 0.6)
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001, # max euler
        # dt = 0.001*5 * 1.55,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(3, 5, 50),
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
    #     # folder_path="ring_intersect/data_high_den/phystem_data",
    #     # folder_path="ring_intersect/data",
    #     folder_path="ring_intersect/data_cluster/data_max_windows/phystem_data",
    #     # folder_path="ring_intersect/data_hd_test/phystem_data",
    #     override_cfgs=False,
    # )
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    # RunType.COLLECT_DATA: collect_data_cfg,
    # RunType.SAVE_VIDEO: save_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type],
    other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)
sim.run()
