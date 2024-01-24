from math import ceil

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring import collect_pipelines

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph import GraphCfg


dynamic_cfg = RingCfg(
    spring_k=6,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.000, # Círculo
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
    angle=[pi/4, -3*pi/4, 3*pi/4, -pi/4],
    center=[
        [-a * radius, -a * radius], 
        [a * radius, a * radius], 
        [a * radius, -a * radius], 
        [-a * radius, a * radius], 
    ]
)

seed = 40028922
seed = None

run_type = RunType.REAL_TIME

num_col_windows=int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6)
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001, # max euler
        # dt = 0.001*5 * 1.55,
        particle_win_cfg=ParticleWindows(
            num_cols=num_col_windows, num_rows=num_col_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(3, 3, 200),
    ),
    num_steps_frame=400,
    fps=600,
    graph_cfg = GraphCfg(
        show_circles      = True,
        show_f_spring     = False,
        show_f_vol        = False,
        show_f_area       = False,
        show_f_total      = False,
        show_center_mass  = True,
        show_inside       = True,
        begin_paused      = False,
        pause_on_high_vel = False,
        cpp_is_debug      = True,
    ),
    # checkpoint=CheckpointCfg(
    #     # folder_path="ring_intersect/data_high_den/phystem_data",
    #     # folder_path="ring_intersect/data",
    #     folder_path="ring_intersect/data_cluster/data_max_windows/phystem_data",
    #     # folder_path="ring_intersect/data_hd_test/phystem_data",
    #     override_cfgs=False,
    # )
)
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
        particle_win_cfg=ParticleWindows(
            num_cols=num_col_windows, num_rows=num_col_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(3, 3, 30),
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

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
