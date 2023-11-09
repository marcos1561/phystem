from phystem.core.run_config import RealTimeCfg, SaveCfg

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
    dt=0.1,
    num_steps_frame=1,
    fps=60,
)

# run_cfg = SaveCfg(
#     path="gif/random_walk.gif",
#     speed=4,
#     fps=60,
#     dt=0.1,
#     duration=10,
# ) 

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg)
sim.run()