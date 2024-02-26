from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import RealTimeCfg
from phystem.systems.ring.ui import graph

cfgs = Simulation.load_cfg("data/config.yaml")


cfgs["dynamic_cfg"].area_potencial = "format"

cfgs["run_cfg"] = RealTimeCfg(
    int_cfg = cfgs["run_cfg"].int_cfg,
    graph_cfg=graph.GraphCfg(),
    num_steps_frame=1000,
    fps=60,
)

sim = Simulation(**cfgs)
sim.run()