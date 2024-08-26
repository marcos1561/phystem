from phystem.systems.ring import Simulation, run_config, collectors

autosave_path = "../datas/test_delta/autosave"

cfgs = Simulation.configs_from_autosave(autosave_path)

run_cfg: run_config.CollectDataCfg = cfgs["run_cfg"]

run_cfg.tf += 400
run_cfg.folder_path = "../datas/test_delta_2"
run_cfg.func = collectors.ColManager.get_pipeline({
    "delta": collectors.DeltaCol,
    "den_vel": collectors.DenVelCol,
    "cr": collectors.CreationRateCol,
})
run_cfg.checkpoint = run_config.CheckpointCfg(autosave_path, 
    override_cfgs=True, ignore_autosave=True, set_time=True)

Simulation(**cfgs).run()