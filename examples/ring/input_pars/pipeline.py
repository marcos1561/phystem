import time
from pathlib import Path

from phystem.utils import progress
from phystem.utils.timer import TimerCount
from phystem.core.run_config import CollectDataCfg
from phystem.core import collectors
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState

from density_vel_col import DensityVelCol
from delta_col import DeltaCol
from creation_rate_col import CreationRateCol 

class ColManager:
    def __init__(self, delta_cfg, den_vel_cfg, creation_rate_cfg,
        solver, path, configs, autosave_cfg: collectors.ColAutoSaveCfg, is_autosave=False):
        path = Path(path)

        path.mkdir(exist_ok=True)

        self.delta_col = DeltaCol(delta_cfg["delta_wait_time"], delta_cfg["delta_wait_dist"], 
            delta_cfg["xlims"], delta_cfg["edge_k"],
            solver, path / "delta", configs,
            autosave_cfg=collectors.ColAutoSaveCfg(to_save_state=False),
            to_debug=delta_cfg["debug"],
        )
        self.den_vel_col = DensityVelCol(den_vel_cfg["xlims"], den_vel_cfg["vel_dt"], den_vel_cfg["den_dt"],
            solver, path / "den_vel", configs,
            autosave_cfg=collectors.ColAutoSaveCfg(to_save_state=False),
        )
        
        self.creation_rate_col = CreationRateCol(creation_rate_cfg["wait_time"], creation_rate_cfg["collect_time"],
            creation_rate_cfg["collect_dt"], 0,
            solver, path / "creation_rate", configs,
            autosave_cfg=collectors.ColAutoSaveCfg(to_save_state=False),
        )
        
        self.solver = solver
        self.autosave_last_time = self.solver.time
        self.autosave_cfg = autosave_cfg
        autosave_path = Path(path) / autosave_cfg.root_dir
        self.state_col = LastState(solver, autosave_path, configs)

        self.timer_count = TimerCount(["delta", "den_vel", "cr"])

        if is_autosave:
            self.delta_col.load_autosave()
            self.den_vel_col.load_autosave()
            self.creation_rate_col.load_autosave()
    
    def collect(self):
        self.timer_count.update(self.delta_col.collect, "delta")
        self.timer_count.update(self.den_vel_col.collect, "den_vel")
        self.timer_count.update(self.creation_rate_col.collect, "cr")
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
        
            solver.cpp_solver.sim_time = metadata["time"] 
            solver.cpp_solver.num_time_steps = metadata["num_time_steps"] 

    print("\nIniciando simulação")
    t1 = time.time()

    den_vel_cfg = cfg["den_vel"]
    delta_cfg = cfg["delta"]
    creation_rate_cfg = cfg["creation_rate"]

    autosave_cfg = collectors.ColAutoSaveCfg(cfg["autosave_dt"])

    col_manager = ColManager(delta_cfg, den_vel_cfg, creation_rate_cfg,
        solver, collect_cfg.folder_path, sim.configs,
        autosave_cfg, is_autosave)

    end_time = collect_cfg.tf
    prog = progress.Continuos(end_time)

    if cfg["time_it"]:
        timer_count = TimerCount(["solver", "col", "autosave"])
        while solver.time < end_time:
            timer_count.update(solver.update, "solver")
            timer_count.update(col_manager.collect, "col")
            timer_count.update(col_manager.check_autosave, "autosave")
            prog.update(solver.time)
    else:
        while solver.time < end_time:
            solver.update()
            col_manager.collect()
            col_manager.check_autosave()
            prog.update(solver.time)

    col_manager.save()

    t2 = time.time()
    from datetime import timedelta
    
    if cfg["time_it"]:
        print()

        elapsed_time = col_manager.timer_count.get_elapsed_time()
        for name, total_time in col_manager.timer_count.total_time.items():
            print(f"{name}: {total_time:.5f} | {total_time/elapsed_time:.4f}")
        
        print("===")
        
        for name, total_time in col_manager.delta_col.timer_count.total_time.items():
            print(f"{name}: {total_time:.5f} | {total_time/col_manager.timer_count.total_time['delta']:.4f}")
        
        print("===")
        
        elapsed_time = timer_count.get_elapsed_time()
        for name, total_time in timer_count.total_time.items():
            print(f"{name}: {total_time:.5f} | {total_time/elapsed_time:.4f}")
        
        print("===")
    
    print("Elapsed time:", timedelta(seconds=t2-t1))