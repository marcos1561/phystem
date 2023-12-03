from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import UpdateType, RunType, RealTimeCfg, SaveCfg, CollectDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg

dynamic_cfg = RingCfg(
    spring_k=4,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    # p0=3.5449077018, # Círculo
    p0=3.65, # Círculo
    # area0=53,

    exclusion_vol=1,
    diameter=1,
    
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
k = 1.4
radius = 20/6 * 1.5
num_rings = n**2
l = 2 * k * radius

space_cfg = SpaceCfg(
    size = n * l,
)
seed = 40028922
# seed = None

np.random.seed(seed)

centers = []
for j in range(n):
    y = k * radius + j * l - space_cfg.size/2
    for i in range(n):
        x = k * radius + i * l - space_cfg.size/2
        centers.append([x, y])

creator_cfg = CreatorCfg(
    num_rings = num_rings,
    num_p = 30,
    r = radius,
    angle=np.random.random(num_rings)*2*pi,
    center= centers,
)


run_type = RunType.REAL_TIME

num_windows = int(0.72 * ceil(space_cfg.size/(dynamic_cfg.diameter*3)))
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        # dt = 0.001*5, # max euler
        dt = 0.001,
        num_col_windows=int(ceil(space_cfg.size/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.WINDOWS,
    ),
    num_steps_frame = 200,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles     = True,
        show_f_spring    = False,
        show_f_vol       = False,
        show_f_area      = False,
        show_f_total     = False,
        show_center_mass = True,
        show_inside      = True,
        begin_paused=False,
        cpp_is_debug=True,
    ),
    # checkpoint=CheckpointCfg(
    #     folder_path="stress/checkpoint",
    #     override_cfgs=True,
    # ),
)

save_cfg = SaveCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001,
        num_col_windows=int(ceil(space_cfg.size/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.WINDOWS,
    ),
    path = "stress/video_test2.mp4",
    speed=2,
    fps=30, 
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
        num_col_windows=int(ceil(space_cfg.size/(dynamic_cfg.diameter*1.2)) * 0.6),
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.WINDOWS,
    ),
    tf = 10,
    folder_path= "stress/checkpoint",
    func=quick_collect,
)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg,
    RunType.COLLECT_DATA: collect_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
