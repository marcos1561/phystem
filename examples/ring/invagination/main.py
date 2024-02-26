from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import RunType, RealTimeCfg, SaveCfg, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows

dynamic_cfg = RingCfg(
    spring_k=5,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    k_area=2,
    
    k_format=0.1,
    p0_format=3.5449077018,
    
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo
    # p0=3.7,
    # area0=53,

    k_invasion= 12,

    diameter=1,
    max_dist=1+0.166,
    rep_force=30,
    adh_force=25,
    
    relax_time=100,
    mobility=1,
    vo=1,
    
    trans_diff=0.1*0,
    rot_diff=0.1,
)


# seed = 40028922
seed = None

creator_cfg = InvaginationCreatorCfg(
    num_rings=30, #13,
    height=8,
    length=15,
    diameter=dynamic_cfg.diameter,
)

space_cfg = SpaceCfg(
    height = creator_cfg.ring_radius * 6,
    length = creator_cfg.ring_radius * 6
    # height = creator_cfg.height * dynamic_cfg.diameter * 13,
    # length = creator_cfg.num_rings * creator_cfg.length * dynamic_cfg.diameter * 2
    # height = 30,
    # length = 30,
)

inv_cfg = InvaginationCfg(
    upper_k=dynamic_cfg.spring_k * 1,
    bottom_k=dynamic_cfg.spring_k * 1,
)


run_type = RunType.SAVE_VIDEO


from math import ceil
num_windows = int(0.72 * ceil(space_cfg.length/(dynamic_cfg.diameter*3)))
n = 10
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001*5,
        particle_win_cfg=ParticleWindows(
            num_cols=num_windows, num_rows=num_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.INVAGINATION,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n, update_freq=100, disable=False),
    ),
    num_steps_frame = 800,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles     = True,
        show_f_spring    = False,
        show_f_vol       = False,
        show_f_area      = False,
        show_f_total     = False,
        show_center_mass = False,
        show_inside      = True,
        begin_paused     = False,
    ),
    checkpoint=CheckpointCfg(
        folder_path="init_loop",
        override_cfgs=True,
    ),
)

save_cfg = SaveCfg(
     int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001*5,
        particle_win_cfg=ParticleWindows(
            num_cols=num_windows, num_rows=num_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.INVAGINATION,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n, update_freq=100, disable=False),
    ),
    path = "./loop_normal.mp4",
    fps=30, 
    speed=100,
    tf=2200,
    graph_cfg = GraphCfg(
        show_circles  = False,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
    ),
    checkpoint=CheckpointCfg(
        folder_path="init_loop",
        override_cfgs=True,
    ),
)

collect_cfg = CollectDataCfg(
     int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001,
        particle_win_cfg=ParticleWindows(
            num_cols=num_windows, num_rows=num_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.INVAGINATION,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n, update_freq=100, disable=False),
    ),
    tf=30,
    folder_path="init_loop",
    func=collect_pipelines.last_state
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg,
    RunType.COLLECT_DATA: collect_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], 
                other_cfgs={"invagination": inv_cfg}, rng_seed=seed)
sim.run()
