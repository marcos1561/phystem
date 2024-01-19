from math import ceil

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring import collect_pipelines

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType
from phystem.systems.ring.ui.graph import GraphCfg


dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.0, # Círculo
    # area0=53,

    exclusion_vol=1,
    diameter=1,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)


space_cfg = SpaceCfg(
    height = 1*30,
    length = 2*30,
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
    obstacle_r  = space_cfg.length/8,
    obstacle_x  = space_cfg.length/8/2,
    obstacle_y  = space_cfg.length/8/2,
    create_length = radius * 4,
    remove_length = radius * 4,
    num_max_rings = 100, 
)

seed = 40028922
seed = None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001, # max euler
        # dt = 0.001*5 * 1.55,
        num_col_windows=int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(6, 100),
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

# from math import cos, pi
# print(dynamic_cfg.diameter/(2 * (1 - cos(2*pi/creator_cfg.num_p)))**.5)
# # dynamic_cfg.diameter / sqrt(2. * (1. - cos(2.*M_PI/((double)num_particles))));
# a = (2 * (1 - cos(2*pi/creator_cfg.num_p)))**.5
# print(dynamic_cfg.diameter/a)
# exit()  

replay_data_cfg = None
if run_type is RunType.REPLAY_DATA:
    replay_data_cfg = ReplayDataCfg(
        directory="data/ring/teste",
        num_steps_frame=1,
        frequency=0,
        graph_cfg=GraphCfg(),
        system_cfg = {
            "creator_cfg": creator_cfg,
            "dynamic_cfg": dynamic_cfg,
            "space_cfg": space_cfg
        },
    )

collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001,
        num_col_windows=int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_NORMAL,
    ),
    tf=3,
    folder_path="checkpoint/data",
    func = collect_pipelines.checkpoints,
    # func_id = collect_pipelines.FuncID.state,
    # get_func= collect_pipelines.get_func,
    # func_cfg = collect_pipelines.CollectPlCfg(
    #     only_last=False, 
    # ),
    func_cfg = collect_pipelines.CheckPointCfg(
        num_checkpoints=20, 
    ),
)

save_cfg = SaveCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001, # max euler
        # dt = 0.001*5 * 1.55,
        num_col_windows=int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(3, 30),
    ),
    # path = "data/videos/teste2.mp4",
    path = "./collision_test.mp4",
    speed=3,
    fps=30, 
    # duration=10,
    tf=60,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
    ),
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: save_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type],
    other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)
sim.run()
