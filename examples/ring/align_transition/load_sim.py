from phystem.systems.ring import Simulation
from phystem.systems.ring import Simulation
from phystem.systems.ring.run_config import RealTimeCfg, CheckpointCfg
from phystem.systems.ring.ui.graph import graphs_cfg

run_cfg = RealTimeCfg(
    int_cfg=None,
    num_steps_frame=1,
    graph_cfg=graphs_cfg.SimpleGraphCfg(
        begin_paused=True,
    ),
    checkpoint=CheckpointCfg("data/delta_test/001/1/autosave")
)

configs = Simulation.configs_from_checkpoint(run_cfg)
Simulation(**configs).run()