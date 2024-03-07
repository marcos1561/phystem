from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.systems.ring.ui import graphs_cfg
from phystem.systems.ring.simulation import Simulation

run_cfg = ReplayDataCfg(
    directory="/home/marcos/Documents/Programacao/IC/dirdip/demos/data/big_snaps",
    data_dir="snaps",
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        # scatter_kwargs={"s": 0.1, "c":"black"}, 
        scatter_kwargs={"s": 0.1}, 
        x_lims=(-300, 300),
        begin_paused=False,
        vel_colors=False,
    ),
    solver_cfg={
        "mode": "same_ids_pre_calc",
    },
    num_steps_frame=3,
)

save_cfg = SaveCfg(
    int_cfg=run_cfg.int_cfg, 
    path="./direction_color.mp4", 
    fps=30,
    # ti=3000,
    # tf=3509.50,
    duration=15,
    speed=1, 
    replay=run_cfg,
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        scatter_kwargs={"s": 0.1}, 
        x_lims=(-300, 300),
        begin_paused=False,
    ),
)

configs = run_cfg.system_cfg
# configs["run_cfg"] = save_cfg

sim = Simulation(**configs)
sim.run()