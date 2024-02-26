from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *

from phystem.core.run_config import UpdateType, RunType, CollectDataCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg

import pipeline

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_area=2,
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
n = 10
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
seed = None

run_type = RunType.COLLECT_DATA

num_col_windows = int(0.6 * ceil(space_cfg.size/(dynamic_cfg.diameter*3)))
collect_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.001,
        num_col_windows=num_col_windows,
        windows_update_freq=1,
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
    ),
    tf = 10,
    folder_path="data",
    func=pipeline.collect_times,
    func_cfg={
        "num_points": 1000,
        "file_name": "times",
    }
)

run_type_to_cfg = {
    RunType.COLLECT_DATA: collect_cfg,
}

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
