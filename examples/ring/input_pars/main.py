from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graphs_cfg import *
from phystem.systems.ring import utils
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
    p0=3.5449077018*1.0, # Círculo
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 12,
    adh_force = 20,
    
    relax_time=0.5,
    mobility=1,
    vo=1,
    
    trans_diff=0,
    rot_diff=0.1,
)

space_cfg = SpaceCfg(
    height = 1.5*30,
    length = 3*30,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 15,
    r = None, angle = [], center = [],
)

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p) 
stokes_cfg = StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0*100 + 0*space_cfg.length/8/2,
    obstacle_y  = 0*space_cfg.length/8/2,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 2, 
    obs_force = 15,
    num_max_rings = 400, 
)

##
## Select Run Type
##
run_type = RunType.REAL_TIME

print(2*radius)
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
    tf=150,
    folder_path="data/teste2",
    func=pipeline.collect_pipeline,
    func_cfg={
        "time_it": False,
        "autosave_dt": 1,
        "den_vel": {
            "xlims": (-20, -20+2*radius),
            "vel_dt": 0.5,
            "den_dt": 0.5,
        },
        "delta": {
            "delta_wait_time": radius*2 * 5,
            # "delta_wait_dist": radius*2 * 1,
            # "xlims": (-2*radius, 0),
            "delta_wait_dist": 24.04867172372065,
            "xlims": (-185.174772272649, -180.36503792790487),
            "edge_k": 1.4,
            "debug": True,
        },
        "creation_rate": {
            "wait_time": 10,
            "collect_time": 90,
            "collect_dt": 0.5,
        },
    },
    checkpoint=CheckpointCfg("data/teste/autosave")
    # checkpoint=CheckpointCfg("../flux_creation_rate/data/init_state_low_flux_force/checkpoint")
)
# collect_data_cfg.checkpoint.configs["dynamic_cfg"] = dynamic_cfg

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=100,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        begin_paused=False,
        show_density=False,
        show_rings=True,
        rings_kwargs={"s": 1},
        density_kwargs={"vmin": -1, "vmax":1},
        cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
        ax_kwargs={"title": "t=8000"},
        cell_shape=[3, 3],
    ),
    ui_settings=UiSettings(
        always_update=False,
        dpi=200,
    ),
    # checkpoint=CheckpointCfg("data/little_adh_3/autosave")
    # checkpoint=CheckpointCfg("../flux_creation_rate/data/init_state_low_flux_force/checkpoint")
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
}

configs = {
    "creator_cfg": creator_cfg, "dynamic_cfg": dynamic_cfg, 
    "space_cfg": space_cfg, "run_cfg": run_type_to_cfg[run_type],
    "other_cfgs": {"stokes": stokes_cfg}
}


sim = Simulation(**configs)
sim.run()

# import cProfile
# cProfile.run("sim.run()", "stats")