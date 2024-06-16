from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring import collectors
from phystem.core.run_config import RunType, CheckpointCfg, CollectDataCfg, RealTimeCfg
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graphs_cfg import *
from phystem.systems.ring import utils
from phystem.gui_phystem.config_ui import UiSettings

from pipeline import collect_pipeline

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    
    k_format=0.03,
    p0_format=3.5449077018*1.0, # Círculo
    
    k_area=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018*1.0, # Círculo
    # p0=3.5449077018*0.9, # Círculo
    # area0=53,

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 12,
    adh_force = 20,
    
    relax_time=2,
    mobility=1,
    vo=1,
    
    trans_diff=0,
    rot_diff=1,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_p = 15,
    r = None, angle = [], center = [],
)

scale_factor = 1/5
radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p) 


space_cfg = SpaceCfg(
    height = scale_factor * 50 * 2*radius,
    length = scale_factor * 200 * 2*radius,
)

num_ring_in_rect = utils.num_rings_in_rect(2*radius, space_cfg)
stokes_cfg = StokesCfg(
    obstacle_r  = scale_factor * 15/2 * 2*radius,
    obstacle_x  = 0,
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

tf = 2000
start_x = scale_factor * (-75/2 - 1) * 2*radius
xlims = [start_x, start_x + 2*radius]

collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01/3,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    ), 
    tf=tf,
    folder_path="datas/test",
    func=collectors.ColManager.get_pipeline({
            "delta": collectors.DeltaCol,
            "den_vel": collectors.DenVelCol,
            "cr": collectors.CreationRateCol,
            "snaps": collectors.SnapshotsCol,
    }),
    # func=collect_pipeline,
    func_cfg={
        "delta": {
            "wait_dist": stokes_cfg.obstacle_r,  
            "xlims": xlims,
            "start_dt": (xlims[1] - xlims[0]) * dynamic_cfg.vo,
            "check_dt": 1/4 * (xlims[1] - xlims[0]) * dynamic_cfg.vo,
        },
        "den_vel": {
            "xlims": xlims,
            "vel_dt": 2,
            "density_dt": 2,
            "vel_frame_dt": 0.5,
        },
        "cr": {
            "wait_time": 0,
            "collect_time": tf, 
            "collect_dt": 2,
        },
        "snaps": {
            "col_cfg": collectors.SnapshotsColCfg(snaps_dt=5),
        },
        "autosave_cfg": ColAutoSaveCfg(freq_dt=10),
    },
    # checkpoint=CheckpointCfg("datas/init_state", override_cfgs=True),
    # checkpoint=CheckpointCfg("datas/low_align/autosave"),
)

real_time_cfg = RealTimeCfg(
    int_cfg=collect_data_cfg.int_cfg,
    num_steps_frame=100*4,
    fps=30,
    # graph_cfg = SimpleGraphCfg(
    #     begin_paused=False,
    #     show_density=False,
    #     show_rings=True,
    #     rings_kwargs={"s": 1},
    #     density_kwargs={"vmin": -1, "vmax":1},
    #     cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
    #     cell_shape=[3, 3],
    # ),
    graph_cfg=MainGraphCfg(
        begin_paused=True,
    ),
    ui_settings=UiSettings(
        always_update=False,
        # dpi=200,
    ),
    checkpoint=CheckpointCfg("datas/explore_p0/14/autosave")
    # checkpoint=CheckpointCfg("../flux_creation_rate/data/init_state_low_flux_force/checkpoint")
)
# real_time_cfg.checkpoint.configs["run_cfg"].int_cfg.dt = 0.01/2

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

if run_type is RunType.REAL_TIME:
    sim = Simulation(**configs)
    sim.run()
elif run_type is RunType.COLLECT_DATA:
    import explore
    explore.main(configs)


# from phystem.systems.ring.quantities import calculators
# data_path = collect_data_cfg.folder_path
# calculators.DeltaCalculator(data_path / "delta").crunch_numbers(to_save=True)
# calculators.DenVelCalculator(data_path / "den_vel").crunch_numbers(to_save=True)