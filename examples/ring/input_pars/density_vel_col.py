import numpy as np
import os, yaml
from pathlib import Path

from phystem.core.collectors import Collector, ColAutoSaveCfg
from phystem.core.solvers import SolverCore

from phystem.systems.ring import utils 
from phystem.systems.ring.collectors import RingCol
from phystem.systems.ring.quantities.datas import BaseData
from phystem.systems.ring.solvers import CppSolver

class DensityVelData(BaseData):
    def __init__(self, root_path: str | Path) -> None:
        super().__init__(root_path)

        self.vel = np.load(self.data_path / "vel.npy")
        self.vel_time = np.load(self.data_path / "vel_time.npy")
        self.den = np.load(self.data_path / "den.npy")
        self.den_time = np.load(self.data_path / "den_time.npy")

        with open(self.data_path / "den_vel_metadata.yaml", "w") as f:
            self.densty_eq = yaml.unsafe_load(f)["density_eq"]

class DensityVelCol(RingCol):
    def __init__(self, xlims, vel_dt, density_dt, solver: CppSolver, path: str | Path, configs: dict, 
        autosave_cfg: ColAutoSaveCfg = None, load_autosave=False) -> None:
        '''Coleta a densidade de equilíbrio e o parâmetro de alinhamento da velocidade (V),
        na região definida pelos limites no eixo x em `xlims`.

        Parâmetros:
        ----------
            xlims:
                Limites no eixo x que definem a região onde a coleta
                é realizada.    
        
            vel_dt:
                Período de tempo entre duas coletas de dados para V.
        
            density_dt:
                Período de tempo entre duas coletas de dados para a densidade.
        '''
        super().__init__(solver, path, configs, autosave_cfg)
        ##
        # Configuration
        ##
        self.xlims = xlims
        self.vel_dt = vel_dt
        self.den_dt = density_dt

        l = xlims[1] - xlims[0]
        h = configs["space_cfg"].height
        ring_r = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p)

        self.density_eq = l * h / (np.pi * ring_r**2)

        ##
        # State
        ##
        self.last_time_den = self.solver.time
        self.last_time_vel = self.solver.time

        ##
        # Data
        ##
        self.density_arr = []
        self.time_den_arr = []
        self.vel_arr = []
        self.time_vel_arr = []

        if load_autosave:
            self.load_autosave()

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

    def get_vel(self):
        return np.array(self.solver.vel)

    def col_vel(self, time, ids, mask):
        self.last_time_vel = time
        
        vel = self.get_vel()[ids][mask]
        vel = vel.reshape(vel.shape[0] * vel.shape[1], vel.shape[2])
        speed = np.sqrt(np.square(vel).sum(axis=1))

        speed[speed == 0] = 1
        # print(speed)

        vel_mean = (vel/speed.reshape(-1, 1)).sum(axis=0) / vel.shape[0]
        self.vel_arr.append((vel_mean[0]**2 + vel_mean[1]**2)**.5)
        self.time_vel_arr.append(time)

    def save(self):
        vel_data_path = self.data_path / "vel.npy"
        vel_time_path = self.data_path / "vel_time.npy"
        den_data_path = self.data_path / "den.npy"
        den_time_path = self.data_path / "den_time.npy"

        np.save(vel_data_path, np.array(self.vel_arr))
        np.save(vel_time_path, np.array(self.time_vel_arr))
        np.save(den_data_path, np.array(self.density_arr))
        np.save(den_time_path, np.array(self.time_den_arr))

        with open(self.data_dir / "den_vel_metadata.yaml", "w") as f:
            yaml.dump({
                "density_eq": self.density_eq
            }, f)

class DensityVelColOld(Collector):
    save_name = "col_state.pickle"

    def __init__(self, xlims, vel_dt, density_dt,
        solver: SolverCore, path: str, configs: dict,
        autosave_cfg: ColAutoSaveCfg=None,
        ) -> None:
        super().__init__(solver, path, configs, autosave_cfg)

        self.data_dir = Path(self.root_path) / "data"
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

    def get_vel(self):
        return np.array(self.solver.vel)

    def col_vel(self, time, ids, mask):
        self.last_time_vel = time
        
        vel = self.get_vel()[ids][mask]
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