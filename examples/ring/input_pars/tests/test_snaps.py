from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg
from phystem.core.run_config import RealTimeCfg, CollectDataCfg
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.collectors import SnapshotsCol, SnapshotsColCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph.graphs_cfg import *
from phystem.systems.ring import utils
from phystem.gui_phystem.config_ui import UiSettings
import pipeline

dynamic_cfg = RingCfg(
    spring_k=20,
    spring_r=0.7,
    
    area_potencial="target_area",
    
    k_area=3,
    p0=4,

    k_invasion = 13,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 20,
    adh_force = 3,
    
    relax_time=0.5,
    mobility=1,
    vo=0.5,
    
    trans_diff=0,
    rot_diff=0.8,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_particles = 10,
    r = None, angle = [], center = [],
)

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles) 

space_cfg = SpaceCfg(
    height = 7 * 2*radius,
    length = 15 * 2*radius,
)

num_ring_in_rect = utils.num_rings_in_rect(2*radius, space_cfg)
stokes_cfg = StokesCfg(
    obstacle_r  = 0.5 * space_cfg.height/2,
    obstacle_x  = 1*1000,
    obstacle_y  = 0,
    create_length = 2.01 * radius,
    remove_length = 2.01 * radius,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(1.1 * num_ring_in_rect), 
)

##
## Select Run Type
##
run_type = RunType.COLLECT_DATA

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
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50, 4),
    ), 
    tf=100,
    folder_path="datas/snaps_teste",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=0.2,
        xlims=(-10, 10),
        autosave_cfg=ColAutoSaveCfg(freq_dt=10),
    ),
    checkpoint=CheckpointCfg("datas/snaps_teste/autosave"),
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=100,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        begin_paused=True,
        show_density=False,
        show_scatter=True,
        scatter_kwargs={"s": 1},
        density_kwargs={"vmin": -1, "vmax":1},
        cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
        ax_kwargs={"title": "t=8000"},
        cell_shape=[3, 3],
    ),
    # graph_cfg=MainGraphCfg(
    #     begin_paused=True,
    # ),
    ui_settings=UiSettings(
        always_update=False,
        # dpi=200,
    ),
    # checkpoint=CheckpointCfg("datas/init_state_flux-0_5/checkpoint"),
    # checkpoint=CheckpointCfg("datas/adh_1/autosave"),
    # checkpoint=CheckpointCfg("../flux_creation_rate/data/init_state_low_flux_force/checkpoint")
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
}

configs = {
    "creator_cfg": creator_cfg, "dynamic_cfg": dynamic_cfg, 
    "space_cfg": space_cfg, "run_cfg": run_type_to_cfg[run_type],
    "other_cfgs": {"stokes": stokes_cfg},
    "rng_seed": 238531723,
}

sim = Simulation(**configs)
sim.run()