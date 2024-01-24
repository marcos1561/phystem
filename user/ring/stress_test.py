from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import RunType, RealTimeCfg, SaveCfg, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    # p0=3.5449077018, # Círculo
    p0=3.7,
    # area0=53,

    diameter=1,
    max_dist=1+0.166,
    rep_force=30,
    adh_force=0.75,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)


from math import pi, ceil
import numpy as np
# n = int((15000)**.5) + 1
n = 5
k = 1.1
radius = 20/6 * 1.5
num_rings = n**2
l = 2 * k * radius

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
    num_p = 30,
    r = radius,
    angle=np.random.random(num_rings)*2*pi,
    center= centers,
)


run_type = RunType.COLLECT_DATA

num_windows = int(0.72 * ceil(space_cfg.length/(dynamic_cfg.diameter*3)))
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001,
        particle_win_cfg=ParticleWindows(
            num_cols=10, num_rows=15,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n+1, update_freq=100, disable=False),
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
        dt = 0.001,
        particle_win_cfg=ParticleWindows(
            num_cols=num_windows, num_rows=num_windows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
    ),
    path = "stress/video_test2.mp4",
    speed=2,
    fps=60, 
    # duration=0.01,
    tf=7,
    num_frames=1*15,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
    ),
)

def quick_collect(sim: Simulation, cfg=None):
    import numpy as np
    np.save("pos.npy", np.array(sim.solver.pos))
    return

collect_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001,
        particle_win_cfg=ParticleWindows(
            num_cols=num_windows, num_rows=num_windows+1,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=n, num_rows_windows=n+1, update_freq=1, disable=False),
    ),
    tf = 1,
    folder_path= "texture/data",
    func=collect_pipelines.last_state,
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg,
    RunType.COLLECT_DATA: collect_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
