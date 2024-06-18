from phystem.systems import ring

configs = ring.Simulation.configs_from_autosave("datas/data3/autosave")
configs["run_cfg"].func = ring.collectors.ColManager.get_pipeline({
    "snaps": ring.collectors.SnapshotsCol
})

sim = ring.Simulation(**configs) 
sim.run()