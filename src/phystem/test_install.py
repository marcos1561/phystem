from phystem.core.run_config import RealTimeCfg, IntegrationCfg

from phystem.systems.random_walker.configs import *
from phystem.systems.random_walker.simulation import Simulation

dynamic_cfg = DynamicCfg(
    vo=1,
    noise_strength= 0.1,
)

space_cfg = SpaceCfg(
    size=10,
)

creator_cfg = CreatorCfg(
    speed=dynamic_cfg.vo,
    size=space_cfg.size,
)

run_cfg = RealTimeCfg(
    IntegrationCfg(
        dt=0.1,
    ),
    num_steps_frame=100,
    fps=80,
)

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg)
sim.run()