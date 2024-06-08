from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.gui_phystem.config_ui import UiSettings

from phystem.systems.ring.ui import graphs_cfg, ui_components
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.solver_config import ReplaySolverCfg

run_cfg = ReplayDataCfg(
    root_path="data/init_state_low_flux_force_snaps/snapshots",
    data_dirname="data",
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        density_kwargs={"vmin": 0, "vmax": 14}, 
        # scatter_kwargs={"s": 0.1, "c":"black", "alpha": 0.1}, 
        scatter_kwargs={"s": 4}, 
        # x_lims=(-300, 300),
        begin_paused=True,
        show_density=False,
        show_rings=True,
        vel_colors=True,
    ),
    solver_cfg= ReplaySolverCfg(
        mode=ReplaySolverCfg.Mode.same_ids,
        ring_per_grid=3, 
    ),
    num_steps_frame=1,
    ui_settings=UiSettings(
        left_pannel_size=0.1,
        always_update=False),
)

save_cfg = SaveCfg(
    int_cfg=run_cfg.int_cfg, 
    path="./data/single_pol.mp4", 
    fps=30,
    dt=0.5,
    ti=0,
    tf=650,
    duration=30,
    replay=run_cfg,
    graph_cfg=graphs_cfg.ReplayGraphCfg(
        # scatter_kwargs={"s": 0.1, "c":"black"}, 
        scatter_kwargs={"s": 1}, 
        # x_lims=(-300, 300),
        vel_colors=True,
    ),
)

configs = run_cfg.system_cfg
# configs["run_cfg"] = save_cfg

sim = Simulation(**configs)
sim.run()