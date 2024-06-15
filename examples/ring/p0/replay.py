from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.systems.ring.ui.graphs_cfg import ReplayGraphCfg
from phystem.systems.ring import Simulation
from phystem.systems.ring.solver_config import ReplaySolverCfg

replay_cfg = ReplayDataCfg(
    root_path="datas/explore_p0/14/snaps",
    graph_cfg=ReplayGraphCfg(
        # show_density=True,
        # vel_colors=True,
        scatter_kwargs={"s": 2},
        colorbar_kwargs={"location": "bottom"},
    ),
    solver_cfg=ReplaySolverCfg(
        mode=ReplaySolverCfg.Mode.same_ids,
        ring_per_grid=3,
    ),
    fps=10,
)

save_cfg = SaveCfg(
    int_cfg=replay_cfg.system_cfg["run_cfg"].int_cfg,
    replay=replay_cfg,
    path="datas/movies/test.mp4",
    fps=30,
    duration=4,
    speed=1,
    dt=1,
)
# replay_cfg.system_cfg["run_cfg"] = save_cfg

Simulation(**replay_cfg.system_cfg).run()