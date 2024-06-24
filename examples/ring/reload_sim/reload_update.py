'''
Carrega uma simulação a partir de um arquivo de configuração
modificando a configuração de execução.
'''
from phystem.core import run_config
configs = run_config.load_configs("config") 

from phystem.systems.ring.ui.graph import graphs_cfg
real_time_cfg = run_config.RealTimeCfg(
    int_cfg=configs["run_cfg"].int_cfg,
    # graph_cfg=graphs_cfg.MainGraphCfg(show_circles=True),
    graph_cfg=graphs_cfg.SimpleGraphCfg(rings_kwargs={"s": 6}),
    num_steps_frame=10,
)
configs["run_cfg"] = real_time_cfg

from phystem.systems.ring import Simulation
sim = Simulation(**configs)
sim.run()