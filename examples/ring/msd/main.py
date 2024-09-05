import numpy as np

from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph.graphs_cfg import *
from phystem.systems.ring import utils

import pipeline


dynamic_cfg = RingCfg(
    spring_k=15,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    # area_potencial="target_area",
    k_area=2,
    k_format=0.1,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.0, # Círculo
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.1666,
    rep_force = 12,
    adh_force = 0.75*0,
    
    relax_time = 100,
    mobility = 1,
    vo = 1,
    
    trans_diff = 0,
    rot_diff   = 0.5,
)

from math import pi, ceil

num_p = 30
n = 10

k = 1.1
radius = utils.get_ring_radius(dynamic_cfg.diameter, num_p)
num_rings = n**2
l = 2 * radius * k

space_cfg = SpaceCfg(
    height = n * l,
    length = n * l,
)

# seed = 40028922
seed = None
np.random.seed(seed)

centers = []
for j in range(n):
    y = k * radius + j * l - space_cfg.length/2
    for i in range(n):
        x = k * radius + i * l - space_cfg.length/2
        centers.append([x, y])

creator_cfg = CreatorCfg(
    num_rings = num_rings,
    num_particles = num_p,
    r = radius,
    angle=np.random.random(num_rings)*2*pi,
    center= centers,
)

space_shape = (space_cfg.height/radius/2, space_cfg.length/radius/2)
stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 0, 
    obs_force = 15,
    num_max_rings = int(space_shape[0] * space_shape[1] * 2), 
)

##
## Select Run Type
##
run_type = RunType.COLLECT_DATA

from math import ceil
num_cols = int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.7)
num_rows = int(ceil(space_cfg.height/(dynamic_cfg.diameter*1.2)) * 0.7)

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
    tf=-1,
    folder_path="data/high_rot",
    func=pipeline.collect_pipeline,
    func_cfg={
        "wait_time": 0,
        "collect_time": 200,
        "dt": 0.5,
    },
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=1,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        begin_paused=False,
        scatter_kwargs={"s": 4},
    ),
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
del configs["other_cfgs"]

for idx, rot_diff in enumerate([0.1, 0.5, 1]):
    dir_name = f"rot_{str(rot_diff).replace('.', '_')}"
    dynamic_cfg.rot_diff = rot_diff
    collect_data_cfg.folder_path = f"data/{dir_name}"
    
    sim = Simulation(**configs)
    sim.run()