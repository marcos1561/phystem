from phystem.core.run_config import RealTimeCfg, CheckpointCfg
from phystem.systems.ring.ui.graphs_cfg import SimpleGraphCfg
from phystem.systems.ring import Simulation

run_cfg = RealTimeCfg(
    int_cfg=None,
    num_steps_frame=10,
    graph_cfg=SimpleGraphCfg(),
    checkpoint=CheckpointCfg("datas/cp1/checkpoint"),
)

run_cfg.checkpoint.configs["space_cfg"].height *= 1.2

cfgs = Simulation.configs_from_checkpoint(run_cfg)
Simulation(**cfgs).run()
