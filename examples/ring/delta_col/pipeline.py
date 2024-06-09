from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import CollectDataCfg
from phystem.utils import progress

from phystem.systems.ring.collectors import DensityVelCol, CreationRateCol, DeltaCol

def collect_pipeline(sim: Simulation, cfg):
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg

    # delta_col = DeltaCol(**cfg["delta"], 
    #     solver=solver, path=collect_cfg.folder_path / "delta", configs=sim.configs,
    #     load_autosave=collect_cfg.is_autosave)

    den_vel_col = DensityVelCol(**cfg["den_vel"],
        solver=solver, root_path=collect_cfg.folder_path, configs=sim.configs,
        load_autosave=collect_cfg.is_autosave)
    
    # cr_col = CreationRateCol(**cfg["cr"],
    #     solver=solver, path=collect_cfg.folder_path / "cr", configs=sim.configs,
    #     load_autosave=collect_cfg.is_autosave)

    prog = progress.Continuos(collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        prog.update(solver.time)
        solver.update()
        
        # delta_col.collect()
        # delta_col.check_autosave()

        den_vel_col.collect()
        den_vel_col.check_autosave()
        
        # cr_col.collect()
        # cr_col.check_autosave()

    # delta_col.save()
    den_vel_col.save()
    # cr_col.save()
    
    prog.update(solver.time)