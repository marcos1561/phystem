from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.ui.graph import graphs_cfg
from phystem.core.run_config import RealTimeCfg, CheckpointCfg

run_cfg = RealTimeCfg(
    int_cfg=None,
    num_steps_frame=1,
    fps=60,
    graph_cfg=graphs_cfg.SimpleGraphCfg(begin_paused=True),
    checkpoint=CheckpointCfg("data_test/checkpoints/cp_3")
)
configs = run_cfg.checkpoint.get_sim_configs(run_cfg)

print(configs["other_cfgs"]["stokes"].flux_force)

Simulation(**configs).run()
