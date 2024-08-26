from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *

from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.run_config import RunType, CheckpointCfg
from phystem.systems.ring.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg

from phystem.systems.ring.ui.graph.graphs_cfg import *
from phystem.systems.ring.solver_config import ReplaySolverCfg
import phystem.systems.ring.utils as ring_utils

from phystem.gui_phystem.config_ui import UiSettings

import pipeline

dynamic_cfg = RingCfg(
    spring_k=20,
    spring_r=1*0.7,
    
    # area_potencial="target_area_and_format",
    area_potencial="target_area",
    k_area=4,
    k_format=0.03,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=4,
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 11,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 20,
    adh_force = 1,
    
    relax_time=1,
    mobility=1,
    vo=0.5,
    
    trans_diff=0.0,
    rot_diff=1,
)
from lovelace.extreme_pars import extreme_configs
dynamic_cfg, stokes_cfgs_dict = extreme_configs.get(align=1, den=1, force=1)
print(dynamic_cfg)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 10,
    r = None, angle = [], center = [],
)

radius = ring_utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p)

space_cfg = SpaceCfg(
    height = 2 * 2*radius,
    length = 10 * 2*radius,
)

space_shape = (space_cfg.height/radius/2, space_cfg.length/radius/2)
print(f"ring radius  : {radius:.2f}")
print(f"channel shape: {space_shape}")

r = 100 * space_cfg.height/2
stokes_cfg = StokesCfg(
    obstacle_r  = r,
    obstacle_x  = r,
    obstacle_y  = 0,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = stokes_cfgs_dict["flux_force"], 
    obs_force = 25,
    num_max_rings = int(space_shape[0] * space_shape[1] * 2), 
)

seed = 40028922
# seed = None


run_type = RunType.REAL_TIME

num_cols, num_rows = ring_utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = ring_utils.rings_grid_shape(space_cfg, radius)

dt = 0.01
collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
            dt = dt,
            particle_win_cfg=ParticleWindows(
                num_cols=num_cols, num_rows=num_rows,
                update_freq=1),
            integration_type=IntegrationType.euler,
            update_type=UpdateType.STOKES,
            in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 20*2, 15),
    ), 
    # tf=250 + 0.5 * 1000 ,
    # tf=space_cfg.length/dynamic_cfg.vo*3 + 0.5*300,
    tf=2000 + 0.5*3,
    folder_path="data/teste",
    func=pipeline.collect_pipeline,
    func_cfg=pipeline.PipelineCfg(
        checkpoint_period=0, 
        snapshot_period=0.5,
        save_type=pipeline.SaveType.snapshot),
    # checkpoint=CheckpointCfg(
    #     root_path="data/init_state_low_flux_force/checkpoint"
    # )
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=30,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        begin_paused=True,
        show_scatter=False,
        show_circles=True,
        show_invasion=True,
        circle_facecolor=True,
        # ax_kwargs={
        #     "xlim": {-space_cfg.length/2, 0},
        # },
    ),
    ui_settings=UiSettings(
        always_update=True,
    ),
    # checkpoint=CheckpointCfg(
    #     root_path="data/init_state_flux-0_5/checkpoint",
    # )
)
# real_time_cfg.checkpoint.configs["dynamic_cfg"].k_area = 1 

video_cfg = SaveCfg(
    int_cfg=collect_data_cfg.int_cfg,
    path="./videos/test2.mp4",
    duration=20,
    # tf=100,
    speed=14,
    fps=30,
    graph_cfg=real_time_cfg.graph_cfg,
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: video_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type],
    other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)

sim.run()
