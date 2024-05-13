import time, os, copy, pickle, yaml
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.utils import progress
from phystem.core.run_config import CollectDataCfg
from phystem.core import collectors
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState
from phystem.systems.ring import utils

from density_vel_col import DensityVelCol
from delta_col import DeltaCol
from creation_rate_col import CreationRateCol 

class ColManager:
    def __init__(self, delta_cfg, den_vel_cfg, creation_rate_cfg,
        solver, path, configs, autosave_cfg: collectors.AutoSaveCfg, is_autosave=False):
        path = Path(path)

        path.mkdir(exist_ok=True)

        self.delta_col = DeltaCol(delta_cfg["delta_wait_time"], delta_cfg["delta_wait_dist"], 
            delta_cfg["xlims"], delta_cfg["edge_k"],
            solver, path / "delta", configs,
            autosave_cfg=collectors.AutoSaveCfg(to_save_state=False),
            to_debug=delta_cfg["debug"],
        )
        self.den_vel_col = DensityVelCol(den_vel_cfg["xlims"], den_vel_cfg["vel_dt"], den_vel_cfg["den_dt"],
            solver, path / "den_vel", configs,
            autosave_cfg=collectors.AutoSaveCfg(to_save_state=False),
        )
        
        self.creation_rate_col = CreationRateCol(creation_rate_cfg["wait_time"], creation_rate_cfg["collect_time"],
            creation_rate_cfg["collect_dt"], 0,
            solver, path / "creation_rate", configs,
            autosave_cfg=collectors.AutoSaveCfg(to_save_state=False),
        )
        
        self.solver = solver
        self.autosave_last_time = self.solver.time
        self.autosave_cfg = autosave_cfg
        autosave_path = Path(path) / autosave_cfg.root_dir
        self.state_col = LastState(solver, autosave_path, configs)

        if is_autosave:
            self.delta_col.load_autosave()
            self.den_vel_col.load_autosave()
            self.creation_rate_col.load_autosave()
    
    def collect(self):
        self.delta_col.collect()
        self.den_vel_col.collect()
        self.creation_rate_col.collect()
        self.check_autosave()

    def check_autosave(self):
        if self.solver.time - self.autosave_last_time > self.autosave_cfg.freq_dt:
            print("Autosave...")

            self.autosave_last_time = self.solver.time

            self.delta_col.autosave()
            self.den_vel_col.autosave()
            self.creation_rate_col.autosave()
            self.state_col.save(metadata={
                "is_autosave": True,
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            })
    
    def save(self):
        self.delta_col.save()
        self.den_vel_col.save()
        self.creation_rate_col.save()

def collect_pipeline(sim: Simulation, cfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    is_autosave = False
    if collect_cfg.checkpoint is not None:
        metadata = collect_cfg.checkpoint.get_metadata()
        
        if metadata.get("is_autosave", False):
            is_autosave = True
        
        # path = os.path.join(collect_cfg.checkpoint.folder_path, "metadata.yaml")
        # with open(path, "r") as f:
        #     metadata = yaml.unsafe_load(f)
        
        solver.cpp_solver.sim_time = metadata["time"] 
        solver.cpp_solver.num_time_steps = metadata["num_time_steps"] 


    print("\nIniciando simulação")
    t1 = time.time()

    den_vel_cfg = cfg["den_vel"]
    delta_cfg = cfg["delta"]
    creation_rate_cfg = cfg["creation_rate"]

    autosave_cfg = collectors.AutoSaveCfg(cfg["autosave_dt"])

    col_manager = ColManager(delta_cfg, den_vel_cfg, creation_rate_cfg,
        solver, collect_cfg.folder_path, sim.configs_container,
        autosave_cfg, is_autosave)

    end_time = collect_cfg.tf
    prog = progress.Continuos(end_time)
    
    while solver.time < end_time:
        solver.update()
        col_manager.collect()
        col_manager.check_autosave()
        prog.update(solver.time)

    col_manager.save()

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))