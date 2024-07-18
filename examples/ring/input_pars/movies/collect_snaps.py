from phystem.systems.ring import collectors, run_config, Simulation

collect_data_cfg = run_config.CollectDataCfg(
    int_cfg=None,
    tf=0.2*50,
    folder_path="datas/snaps/adh_1",
    func=collectors.SnapshotsCol.pipeline,
    func_cfg=collectors.SnapshotsColCfg(
        snaps_dt=0.2,
        xlims=(-124.58 - 3, -121.35 + 24.3),
        autosave_cfg=collectors.ColAutoSaveCfg(freq_dt=10),
    ),
    checkpoint=run_config.CheckpointCfg("../datas/adh_1/autosave", ignore_autosave=True),
)

configs = Simulation.configs_from_checkpoint(collect_data_cfg)
Simulation(**configs).run()


