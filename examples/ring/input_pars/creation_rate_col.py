from pathlib import Path
import numpy as np

from phystem.core.run_config import CollectDataCfg
from phystem.systems.ring.collectors import RingCol

class CreationRateCol(RingCol):
    save_name = "col_state.pickle"

    def __init__(self, wait_time, collect_time, collect_dt, id, solver: collectors.SolverCore, path: str, configs: dict, autosave_cfg: collectors.ColAutoSaveCfg = None) -> None:
        super().__init__(solver, path, configs, autosave_cfg)

        collect_cfg: CollectDataCfg = configs["run_cfg"]
        cfg = collect_cfg.func_cfg

        root_path = Path(path)
        self.data_dir = root_path / "data"
        self.checkpoints_dir = root_path / "checkpoints"

        paths_check = [self.data_dir, self.checkpoints_dir]
        for p in paths_check:
            p.mkdir(exist_ok=True, parents=True)

        if autosave_cfg is not None:
            self.state_col = LastState(self.solver, self.autosave_state_path, self.configs)
            self.autosave_last_time = self.solver.time

        self.id = id
        self.wait_time = wait_time
        self.collect_time = collect_time
        self.collect_dt = collect_dt
        
        self.wait_time_done = False

        self.last_time = self.solver.time
        self.point_id = 0

        self.num_points = int(self.collect_time/self.collect_dt)

        self.time_arr = np.zeros(self.num_points, dtype=np.float32)
        self.num_created_arr = np.zeros(self.num_points, dtype=np.int32)
        self.num_active_arr = np.zeros(self.num_points, dtype=np.int32)

    def collect(self) -> None:
        time = self.solver.time

        if time < self.wait_time:
            return

        if time > self.collect_time + self.wait_time:
            return
        
        if self.point_id > self.num_points-1:
            return

        self.num_created_arr[self.point_id] += self.solver.num_created_rings   
        
        if self.solver.time - self.last_time > self.collect_dt:
            self.last_time = self.solver.time
            self.time_arr[self.point_id] = self.solver.time
            self.num_active_arr[self.point_id] = self.solver.num_active_rings   
            self.point_id += 1
        
    @property
    def vars_to_save(self):
        return ["wait_time_done", "point_id", "last_time", "id"]

    def save_checkpoint(self):
        path = self.checkpoints_dir / f"cp_{self.id}"
        path.mkdir(exist_ok=True)

        cp_collector = LastState(self.solver, path, self.configs)
        cp_collector.save()

    def autosave(self):
        super().autosave()
        self.save(self.autosave_data_path)

    def load_autosave(self):
        # with open(self.autosave_path / self.save_name, "rb") as f:
        #     saved_vars = pickle.load(f)

        # for key, var in self.vars_to_save.items():
        #     var = saved_vars[key]

        # data_arrays = {
        #     "time": self.time_arr,
        #     "num_created": self.num_created_arr,
        #     "num_active": self.num_active_arr,
        # }
        # for name, arr in data_arrays.items():
        #     saved_arr = np.load(os.path.join(self.autosave_data_dir, f"{name}_{self.id}.npy"))
        #     arr[:saved_arr.size] = saved_arr

        super().load_autosave()
        data_arrays = {
            "time": self.time_arr,
            "num_created": self.num_created_arr,
            "num_active": self.num_active_arr,
        }
        for name, arr in data_arrays.items():
            saved_arr = np.load(os.path.join(self.autosave_data_path, f"{name}_{self.id}.npy"))
            arr[:saved_arr.size] = saved_arr

    def save(self, dir=None):
        if dir is None:
            dir = self.data_dir

        import yaml
        metadata = {"num_points": self.point_id}
        with open(os.path.join(dir, "metadata.yaml"), "w") as f:
            yaml.dump(metadata, f)

        np.save(os.path.join(dir, f"time_{self.id}.npy"), self.time_arr)
        np.save(os.path.join(dir, f"num_created_{self.id}.npy"), self.num_created_arr)
        np.save(os.path.join(dir, f"num_active_{self.id}.npy"), self.num_active_arr)
