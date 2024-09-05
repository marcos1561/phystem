from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import RingCfg, CreatorCfg, SpaceCfg
from phystem.systems.ring.run_config import IntegrationCfg, UpdateType
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import CollectDataCfg, SolverType


def generate_normal_data():
    dynamic_cfg = RingCfg(
        spring_k=10,
        spring_r=0.3,
        
        area_potencial="target_area",
        k_area=5,
        # p0=4.828427, # Triângulo retângulo
        # p0=4.55901, # Triângulo equilátero
        # p0=4, # quadrado
        p0=3.5449077018, # Círculo
        area0=40,

        k_invasion=-1,

        diameter  = 1,
        max_dist  = 1 + 0.1666,
        rep_force = 30,
        adh_force = 0.75,

        relax_time=1,
        mobility=1,
        vo=1,
        
        trans_diff=0.1,
        rot_diff=0.1,
    )

    space_cfg = SpaceCfg(
        height = 30,
        length = 30,
    )

    from math import pi
    radius = 20/6 * 1.1
    a = 2
    creator_cfg = CreatorCfg(
        num_rings = 4,
        num_particles = 30,
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
            update_type=UpdateType.PERIODIC_NORMAL,
        ),
        tf = 100,
        folder_path="test_windows",
        func_id = collect_pipelines.FuncID.last_pos,
        get_func= collect_pipelines.get_func,
    )

    sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=collect_data_cfg, rng_seed=seed)
    # sim.save_cfgs("test_windows/config")
    sim.run()

generate_normal_data()