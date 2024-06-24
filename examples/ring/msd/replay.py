from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.gui_phystem.config_ui import UiSettings

from phystem.systems.ring.ui import ui_components
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.solver_config import ReplaySolverCfg
from phystem.systems.ring.ui.graph import graphs_cfg

run_cfg = ReplayDataCfg(
    root_path="data/rot_1",
    data_dirname="data",
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        begin_paused=True,
        # x_lims=(-300, 300),
        show_rings=True,
        vel_colors=False,
        # show_density=True,
        # density_kwargs={"vmin": 0, "vmax": 14}, 
        # scatter_kwargs={"s": 1, "c":"black", "alpha": 0.3}, 
        scatter_kwargs={"s": 1}, 
    ),
    solver_cfg=ReplaySolverCfg(
        mode=ReplaySolverCfg.Mode.same_ids,
        ring_per_grid=3, 
        ),
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