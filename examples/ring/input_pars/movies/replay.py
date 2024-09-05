from phystem.core.run_config import ReplayDataCfg, SaveCfg
from phystem.systems.ring.ui.graph.graphs_cfg import ReplayGraphCfg, ParticleCircleCfg
from phystem.systems.ring import Simulation
from phystem.systems.ring.solver_config import ReplaySolverCfg

replay_cfg = ReplayDataCfg(
    # root_path="datas/explore_p0_2000/11/snaps",
    root_path="datas/snaps/adh_1",
    graph_cfg=ReplayGraphCfg(
        show_density=True,
        show_circles=False,
        show_scatter=False,
        # vel_colors=False,
        x_lims=(-20, 20),
        circles_cfg=ParticleCircleCfg(
            facecolor=True,
            color=ParticleCircleCfg.DEFAULT_COLOR,
        ),
        scatter_kwargs={"s": 1},
        density_kwargs={"vmin": -1, "vmax": 1},
        colorbar_kwargs={"location": "bottom", "label": "Densidade Relativa"},
        cell_shape=(2, 2),
    ),
    solver_cfg=ReplaySolverCfg(
        calc_vel_dframes=5*10,
    ),
    fps=30,
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