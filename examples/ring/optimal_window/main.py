from math import pi, ceil
import numpy as np

from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg

from phystem.core.run_config import RunType
from phystem.systems.ring.run_config import RealTimeCfg, IntegrationType, UpdateType

from pipeline import Pipeline

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_area=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo
    # area0=53,

    exclusion_vol=1,
    diameter=1,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)


n = 5
k = 1.4
radius = 20/6 * 1.5
num_rings = n**2
l = 2 * k * radius

space_cfg = SpaceCfg(
    size = n * l,
)

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

seed = 40028922
seed=None


run_type = RunType.REAL_TIME
run_pipeline = True


num_windows = int(ceil(space_cfg.size/(dynamic_cfg.diameter*3)))
num_windows = int(ceil(space_cfg.size/(dynamic_cfg.diameter*1.2))) 

# print(num_windows)
# exit()

real_time_cfg = RealTimeCfg(
    dt = 0.001,
    num_steps_frame = 400,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
        begin_paused  = False,
        cpp_is_debug  = True,
    ),
    num_col_windows=num_windows,
    update_type      = UpdateType.PERIODIC_WINDOWS,
    integration_type = IntegrationType.euler,
)
print(real_time_cfg.num_col_windows)

run_type_to_cfg = {
    RunType.REAL_TIME: real_time_cfg, 
}

if run_pipeline:
    configs = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed).init_configs 
    pipeline = Pipeline(configs)
    pipeline.run()
else:
    Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed).run()
