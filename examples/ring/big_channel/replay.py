from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.gui_phystem.config_ui import UiSettings

from phystem.systems.ring.ui import graphs_cfg, ui_components
from phystem.systems.ring.simulation import Simulation

run_cfg = ReplayDataCfg(
    directory="/home/marcos/Documents/Programacao/IC/dirdip/demos/data/big_snaps",
    data_dir="snaps",
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        density_kwargs={"vmin": 0, "vmax": 14}, 
        # scatter_kwargs={"s": 0.1, "c":"black", "alpha": 0.1}, 
        scatter_kwargs={"s": 0.1}, 
        x_lims=(-300, 300),
        begin_paused=False,
        show_density=False,
        show_rings=True,
        vel_colors=False,
    ),
    solver_cfg={
        "mode": "normal",
    },
    num_steps_frame=1,
)

# save_cfg = SaveCfg(
#     int_cfg=run_cfg.int_cfg, 
#     path="./data/movies/test3.mp4", 
#     fps=30,
#     dt=0.5,
#     ti=3000,
#     tf=3509.50,
#     duration=15,
#     replay=run_cfg,
#     graph_cfg=graphs_cfg.ReplayGraphCfg(
#         # scatter_kwargs={"s": 0.1, "c":"black"}, 
#         scatter_kwargs={"s": 0.1}, 
#         x_lims=(-300, 300),
#         begin_paused=False,
#         vel_colors=False,
#     ),
# )

configs = run_cfg.system_cfg
# configs["run_cfg"] = save_cfg

sim = Simulation(**configs)
sim.run()