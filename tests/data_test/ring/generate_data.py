from phystem.ring.simulation import Simulation

from phystem.ring.configs import RingCfg, CreateCfg, SpaceCfg
from phystem.ring import collect_pipelines

from phystem.ring.run_config import CollectDataCfg
from phystem.core.run_config import UpdateType, SolverType


def generate_normal_data():
    dynamic_cfg = RingCfg(
        spring_k=10,
        spring_r=0.3,
        
        area_potencial="format",
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
    create_cfg = CreateCfg(
        num_rings = 4,
        num_p = 30,
        r = radius,
        vo = dynamic_cfg.vo,
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
        tf = 100,
        dt = 0.001/2,
        folder_path="normal_data",
        func_id = collect_pipelines.FuncID.last_pos,
        get_func= collect_pipelines.get_func,
        solver_type=SolverType.CPP,
        update_type=UpdateType.NORMAL,
    )

    sim = Simulation(create_cfg, dynamic_cfg, space_cfg, run_cfg=collect_data_cfg, rng_seed=seed)
    sim.run()

generate_normal_data()