from math import ceil

from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.run_config import RunType, CheckpointCfg
from phystem.systems.ring.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg

from phystem.systems.ring.ui.graph.graphs_cfg import SimpleGraphCfg
from phystem.systems.ring import utils
from phystem.gui_phystem.config_ui import UiSettings

from phystem.systems.ring import collect_pipelines
from collect_func import collect_pos

dynamic_cfg = RingCfg(
    spring_k=18,
    spring_r=0.7*0 + 1,
    
    # area_potencial="target_area_and_format",
    area_potencial="target_area",
    k_area=2,
    k_format=0.03,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.9,
    p0_format=3.5449077018*1.0, # Círculo
    # area0=53,

    k_invasion = 15,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 25,
    adh_force = 1,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.0,
    rot_diff=0.8,
)

num_particles = 15
radius = utils.get_ring_radius(dynamic_cfg.diameter, num_particles)

space_cfg = SpaceCfg(
    height = 4 * radius*2,
    length = 4 * radius*2,
)

from math import pi
a = 2
creator_cfg = CreatorCfg(
    num_rings = 4,
    num_particles = num_particles,
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

num_cols, num_rows = utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = utils.rings_grid_shape(space_cfg, radius)

real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_cols,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 6, 50),
    ),
    num_steps_frame=20,
    fps=30,
    graph_cfg=SimpleGraphCfg(
        show_scatter=False,
        show_circles=True,
        circle_facecolor=True,
    ),
    ui_settings=UiSettings(
        always_update=True,
    ),
)


from phystem.systems.ring.collectors import SnapshotsCol, SnapshotsColCfg, ColAutoSaveCfg, ColManager
from phystem.systems.ring.run_config import CheckpointCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=real_time_cfg.int_cfg,
    tf=10,
    folder_path="./datas/data3",
    func=ColManager.get_pipeline({
        "snaps": SnapshotsCol
    }),
    func_cfg={
        "snaps": {"col_cfg": SnapshotsColCfg(snaps_dt=1)},
        "autosave_cfg":ColAutoSaveCfg(freq_dt=3),
    },
    # checkpoint=CheckpointCfg("datas/data3/autosave")
)

save_cfg = SaveCfg(
    int_cfg=real_time_cfg.int_cfg,
    # path = "data/videos/teste2.mp4",
    path = "./collision_test.mp4",
    speed=3,
    fps=30, 
    # duration=10,
    tf=60,
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg,
    RunType.COLLECT_DATA: collect_data_cfg,
    RunType.SAVE_VIDEO: save_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
