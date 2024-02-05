from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import RunType, RealTimeCfg, SaveCfg, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    k_area=2,
    k_format=0.1,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo
    # p0=3.7,
    # area0=53,

    k_invasion= 12,

    diameter=1,
    max_dist=1+0.266,
    rep_force=30,
    adh_force=30,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)


# seed = 40028922
seed = None

creator_cfg = InvaginationCreatorCfg(
    num_rings=13,
    height=8,
    length=9,
    diameter=dynamic_cfg.diameter,
)

space_cfg = SpaceCfg(
    height = creator_cfg.height * dynamic_cfg.diameter * 13,
    length = creator_cfg.num_rings * creator_cfg.length * dynamic_cfg.diameter * 1.1
    # length = creator_cfg.height*dynamic_cfg.diameter*2,
    # height = 300,
    # length = 300,
)

inv_cfg = InvaginationCfg(
    upper_k=dynamic_cfg.spring_k * 3,
    bottom_k=dynamic_cfg.spring_k * 0.2,
)

run_type = RunType.REAL_TIME


from math import ceil
num_windows = int(0.72 * ceil(space_cfg.length/(dynamic_cfg.diameter*3)))
n = 5
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001*5,
        particle_win_cfg=ParticleWindows(
            num_cols=10, num_rows=15,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.INVAGINATION,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n, update_freq=100, disable=False),
    ),
    num_steps_frame = 500,
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
    # checkpoint=CheckpointCfg(
    #     folder_path="texture/data",
    #     override_cfgs=False,
    # ),
)

save_cfg = SaveCfg(
    int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001*5,
        particle_win_cfg=ParticleWindows(
            num_cols=10, num_rows=15,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.INVAGINATION,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n, update_freq=100, disable=False),
    ),
    path = "./invagination.mp4",
    speed=30,
    fps=30, 
    duration=8,
    # tf=3,
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
    RunType.SAVE_VIDEO: save_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], 
                other_cfgs={"invagination": inv_cfg}, rng_seed=seed)
sim.run()
