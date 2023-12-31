from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import RingCfg, CreatorCfg, SpaceCfg
from phystem.systems.ring.run_config import IntegrationCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import CollectDataCfg
from phystem.core.run_config import UpdateType, SolverType


def generate_normal_data():
    dynamic_cfg = RingCfg(
        spring_k=10,
        spring_r=0.3,
        
        area_potencial="target_area",
        k_bend=5,
        # p0=4.828427, # Triângulo retângulo
        # p0=4.55901, # Triângulo equilátero
        # p0=4, # quadrado
        p0=3.5449077018, # Círculo
        area0=40,

        exclusion_vol=1,
        diameter=1,
        
        relax_time=1,
        mobility=1,
        vo=1,
        
        trans_diff=0.1,
        rot_diff=0.1,
    )

    space_cfg = SpaceCfg(
        size = 30,
    )

    from math import pi
    radius = 20/6 * 1.1
    a = 2
    creator_cfg = CreatorCfg(
        num_rings = 4,
        num_p = 30,
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

    collect_data_cfg = CollectDataCfg(
        int_cfg=IntegrationCfg(
            dt=0.001/2,
            update_type=UpdateType.NORMAL,
        ),
        tf = 100,
        folder_path="normal_data",
        func_id = collect_pipelines.FuncID.last_pos,
        get_func= collect_pipelines.get_func,
    )

    sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=collect_data_cfg, rng_seed=seed)
    sim.run()

generate_normal_data()