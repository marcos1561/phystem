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
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    # area_potencial="target_area",
    k_area=2,
    k_format=0.03,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.1, # Círculo
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.1666,
    rep_force = 12,
    adh_force = 0.7,
    
    relax_time=0.5,
    mobility=1,
    vo=1,
    
    trans_diff=0.0,
    rot_diff=0.1,
)

space_cfg = SpaceCfg(
    height = 1*30,
    length = 3*30,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 15,
    r = None, angle = [], center = [],
)

radius = ring_utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p)
space_shape = (space_cfg.height/radius/2, space_cfg.length/radius/2)
print(f"ring radius  : {radius:.2f}")
print(f"channel shape: {space_shape}")

stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(space_shape[0] * space_shape[1] * 2), 
)

seed = 40028922
# seed = None

##
## Select Run Type
##
run_type = RunType.REAL_TIME


# num_cols = int(ceil(space_cfg.length/(dynamic_cfg.diameter*1.2)) * 0.6)
# num_rows = int(ceil(space_cfg.height/(dynamic_cfg.diameter*1.2)) * 0.6)
# num_cols_cm = int(ceil(space_cfg.length / (2.5*radius)))
# num_rows_cm = int(ceil(space_cfg.height / (2.5*radius)))

num_cols, num_rows = ring_utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = ring_utils.rings_grid_shape(space_cfg, radius)

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
    # tf=250 + 0.5 * 1000 ,
    # tf=space_cfg.length/dynamic_cfg.vo*3 + 0.5*300,
    tf=2000 + 0.5*3,
    folder_path="data/teste",
    func=pipeline.collect_pipeline,
    func_cfg=pipeline.PipelineCfg(
        checkpoint_period=0, 
        snapshot_period=0.5,
        save_type=pipeline.SaveType.snapshot),
    checkpoint=CheckpointCfg(
        root_path="data/init_state_low_flux_force/checkpoint"
    )
)

real_time_cfg = RealTimeCfg(
    #  int_cfg=IntegrationCfg(
    #         dt = 0.01,
    #         particle_win_cfg=ParticleWindows(
    #             num_cols=num_cols, num_rows=num_rows,
    #             update_freq=1),
    #         integration_type=IntegrationType.euler,
    #         update_type=UpdateType.STOKES,
    #         in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    # ), 
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=20,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        show_scatter=False,
        show_circles=True,
        circle_facecolor=False,
        rings_kwargs={"s": 1},
        density_kwargs={"vmin": -1, "vmax":1},
        cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
        # circles_color="black",
        cell_shape=[3, 3],
    ),
    ui_settings=UiSettings(
        always_update=True,
        fig_size_scale=1.6,
    ),
    # graph_cfg = MainGraphCfg(
    #     show_circles      = True,
    #     pause_on_high_vel = True,
    # ),
    # checkpoint=CheckpointCfg(
    #     root_path="../flux_creation_rate/data/low_adh_align_flux/autosave"
        # folder_path="../flux_creation_rate/data/init_state_low_flux_force/checkpoint"
        # folder_path="data/init_state_low_flux_force/checkpoint",
    # )
)

# replay_cfg = ReplayDataCfg(
#     directory="data/snapshots",
#     graph_cfg=ReplayGraphCfg(
#         scatter_kwargs={"s": 1},
#         vel_colors=True,
#         show_rings=True,
#         show_cm=False,
#         show_density=False,
#     ),
#     solver_cfg=ReplaySolverCfg(
#         ring_per_grid=3,
#         vel_from_solver=False,
#         mode=ReplaySolverCfg.Mode.same_ids,
#     ),
# )

video_cfg = SaveCfg(
    int_cfg=collect_data_cfg.int_cfg,
    path="./color_test.mp4",
    # duration=5,
    tf=100,
    speed=40,
    fps=30,
    graph_cfg=SimpleGraphCfg(),
    # graph_cfg = MainGraphCfg(
    #     show_circles      = True,
    #     show_f_spring     = False,
    #     show_f_vol        = False,
    #     show_f_area       = False,
    #     show_f_total      = False,
    #     show_center_mass  = True,
    #     show_inside       = False,
    #     cpp_is_debug      = False,
    # ),
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: video_cfg,
    # RunType.REPLAY_DATA: replay_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type],
    other_cfgs={"stokes": stokes_cfg}, rng_seed=seed)

sim.run()
