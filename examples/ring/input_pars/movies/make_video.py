from phystem.systems.ring import collectors, run_config, Simulation

save_cfg = run_config.SaveCfg(
    int_cfg=None,
    path="datas/movies/adh_1/movie.mp4",
    fps=30,
    duration=2,
    speed=1,
    dt=0.01,
    checkpoint=run_config.CheckpointCfg("../datas/adh_1/autosave"),
)

configs = Simulation.configs_from_checkpoint(save_cfg)
Simulation(**configs).run()