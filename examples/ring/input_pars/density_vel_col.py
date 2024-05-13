import numpy as np
import os, pickle
from pathlib import Path

from phystem.core.collectors import Collector, AutoSaveCfg
from phystem.core.solvers import SolverCore

from phystem.systems.ring import utils

class DensityVelCol(Collector):
    save_name = "col_state.pickle"

    def __init__(self, xlims, vel_dt, density_dt,
        solver: SolverCore, path: str, configs: dict,
        autosave_cfg: AutoSaveCfg=None,
        ) -> None:
        super().__init__(solver, path, configs, autosave_cfg)

        self.data_dir = Path(self.path) / "data"
        if not self.data_dir.exists():
            os.mkdir(self.data_dir) 

        self.xlims = xlims
        self.vel_dt = vel_dt
        self.den_dt = density_dt

        l = xlims[1] - xlims[0]
        h = configs["space_cfg"].height
        
        ring_r = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p)

        self.density_eq = l * h / (np.pi * ring_r**2)

        self.last_time_den = self.solver.time
        self.last_time_vel = self.solver.time

        self.density_arr = []
        self.time_den_arr = []
        self.vel_arr = []
        self.time_vel_arr = []

    @property
    def vars_to_save(self):
        return [
            "last_time_den",
            "last_time_vel",
            "density_arr",
            "time_den_arr",
            "vel_arr",
            "time_vel_arr",
        ]

    def collect(self) -> None:
        time = self.solver.time

        exec_vel = time - self.last_time_vel > self.vel_dt
        exec_den = time - self.last_time_den > self.den_dt
        
        if not exec_den and not exec_vel:
            return

        num_active = self.solver.num_active_rings
        ids = self.solver.rings_ids[:num_active]
        cm = np.array(self.solver.center_mass)[ids]
        mask = (cm[:, 0] > self.xlims[0]) & (cm[:, 0] < self.xlims[1])

        mask_sum = mask.sum()
        if mask.sum() == 0:
            return

        if exec_den:
            self.col_density(time, mask_sum)
        if exec_vel:
            self.col_vel(time, ids, mask)

    def col_density(self, time, mask_sum):
        self.last_time_den = time

        self.density_arr.append(mask_sum/self.density_eq)
        self.time_den_arr.append(time)

    def col_vel(self, time, ids, mask):
        self.last_time_vel = time
        
        vel = np.array(self.solver.vel)[ids][mask]
        vel = vel.reshape(vel.shape[0] * vel.shape[1], vel.shape[2])
        speed = np.sqrt(np.square(vel).sum(axis=1))

        speed[speed == 0] = 1
        # print(speed)

        vel_mean = (vel/speed.reshape(-1, 1)).sum(axis=0) / vel.shape[0]
        self.vel_arr.append((vel_mean[0]**2 + vel_mean[1]**2)**.5)
        self.time_vel_arr.append(time)

    def save(self):
        vel_data_path = self.data_dir / "vel.npy"
        vel_time_path = self.data_dir / "vel_time.npy"
        den_data_path = self.data_dir / "den.npy"
        den_time_path = self.data_dir / "den_time.npy"

        np.save(vel_data_path, np.array(self.vel_arr))
        np.save(vel_time_path, np.array(self.time_vel_arr))
        np.save(den_data_path, np.array(self.density_arr))
        np.save(den_time_path, np.array(self.time_den_arr))

        import yaml
        with open(self.data_dir / "den_vel_metadata.yaml", "w") as f:
            yaml.dump({
                "density_eq": self.density_eq
            }, f)