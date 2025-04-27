import numpy as np
import yaml, pickle
from pathlib import Path
from enum import Enum, auto
import numpy as np

from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.collectors import RingCol, ColCfg
from phystem.data_utils.data_types import ArraySizeAware
from phystem.systems.ring.solvers import CppSolver

from .config_to_col import Configs2Collector

class DenVelColCfg(ColCfg):
    def __init__(self, xlims, density_dt, vel_dt=None, pol_dt=None,
        vel_frame_dt=None, transient_time=0, memory_per_file=10*1e6, autosave_cfg = None):
        '''
        Faz duas formas de coleta dos centros de massa na região definida 
        pelos limites no eixo x em `xlims`:
        
        1: Coleta a cada `density_dt` un. de tempo.

        2: Coleta a cada `vel_dt` un. de tempo. Nesse caso, após ter sido feito
        uma coleta, outra é realizada logo após `vel_frame_dt` un. de tempo. Na segunda
        coleta, apenas são salvos os centros de massa dos mesmos anéis presentas na primeira
        coleta. Essas coletas consecutivas são feitas para ser possível calcular a velocidade.

        Também é salvo o tempo em cada ponto coletado.

        Formato dos Dados:
        -----------------
        Ambas formas de coleta (1 e 2) guardam seus dados em um array com dimensão (N, n_p, d) em que:
        
        N   : Número de pontos coletados
        n_p : Número de anéis em um ponto coletado
        d   : Dimensão dos elementos que constituem o ponto

        Sendo `data` o array que contém os dados, um ponto para cada caso é:

        - 1: Os centros de massa dos anéis na região de interesse, então d=2. Portanto

            data[i] -> i-ésimo ponto. Array com dimensão (n_p, 2)
            data[i, :, 0] -> Coordenados no eixo x do i-ésimo ponto
            data[i, :, 1] -> Coordenados no eixo y do i-ésimo ponto
            
        - 2: Os centros de massa dos anéis nas duas coletas separadas por `vel_frame_dt` 
            un. de tempo. Nesse caso d=4

            data[i] -> i-ésimo ponto. Array com dimensão (n_p, 4)
            data[i, :, :2] -> Centros de massa na primeira coleta, digamos no tempo T = t.
            data[i, :, 2:] -> Centros de massa na segunda coleta, no tempo T = t + `vel_frame_dt`.

            A velocidade de todos os pontos, então, é dado por `(data[:,:,2:] - data[:,:,:2])/vel_frame_dt`.

        OBS: Se a coleta for muito longa, os dados coletados vão ser salvos em arquivos separados, mas que em
        conjunto representam uma única lista de pontos de dados.

        Parâmetros:
        ----------
        vel_dt, density_dt, vel_frame_dt, pol_dt:
            Tempos cujas unidades são dadas pelo passo temporal da simulação (`solver.dt`).

        transient_time:
            Tempo esperado para começar as medidas. Sua unidade é a unidade de tempo da simulação.
            
        memory_per_file:
            Tamanho da memória em bytes que o array com os dados terá. Se a coleta
            preencher esse array, o mesmo é salvo na memória e outro array é inicializado.
        '''
        if vel_dt is not None and vel_frame_dt is None:
            raise ValueError(f"`vel_dt` foi dado, mas `vel_frame_dt` não foi dado.")
        
        super().__init__(autosave_cfg)
        self.xlims = xlims
        self.density_dt = density_dt
        self.vel_dt = vel_dt
        self.pol_dt = pol_dt
        self.vel_frame_dt = vel_frame_dt
        self.transient_time = transient_time
        self.memory_per_file = memory_per_file

class DenVelCol(RingCol):
    solver: CppSolver
    col_cfg: DenVelColCfg

    class DataName(Enum):
        velocity = auto()
        density = auto()
        polarity = auto()

    def setup(self):
        # Configuration
        self.xlims = self.col_cfg.xlims
        self.vel_dt = self.col_cfg.vel_dt
        self.den_dt = self.col_cfg.density_dt
        self.vel_frame_dt = self.col_cfg.vel_frame_dt
        self.pol_dt = self.col_cfg.pol_dt
        self.transient_time = self.col_cfg.transient_time

        xlims = self.col_cfg.xlims
        l = xlims[1] - xlims[0]
        h = self.configs["space_cfg"].height
        area_eq = self.configs["dynamic_cfg"].get_equilibrium_area() 
        
        num_max_rings = int(l * h / area_eq * 1.2)
        self.density_eq = 1 / area_eq
        self.num_data_points_per_file = int(self.col_cfg.memory_per_file / (num_max_rings * 2 * 4))

        # State
        self.last_time_den = self.solver.num_time_steps
        self.last_time_vel = self.solver.num_time_steps
        self.last_time_pol = self.solver.num_time_steps
        self.vel_frame = 0
        self.vel_point_data: np.array = None
        self.vel_point_ids: np.array = None 
        self.den_id = 0
        self.vel_id = 0
        self.pol_id = 0

        # Data
        self.den_data = ArraySizeAware.empty()
        if self.den_dt is not None:
            self.den_data = ArraySizeAware(self.num_data_points_per_file, num_max_rings, 2)
        
        self.vel_data = ArraySizeAware.empty()
        if self.vel_dt is not None:
            self.vel_data = ArraySizeAware(self.num_data_points_per_file, num_max_rings, 4)
        
        self.pol_data: ArraySizeAware = ArraySizeAware.empty()
        if self.pol_dt is not None:
            self.pol_data = ArraySizeAware(self.num_data_points_per_file, num_max_rings, 1)
        
        self.time_den_arr = []
        self.time_vel_arr = []
        self.time_vel2_arr = []
        self.time_pol_arr = []
        
    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend([ 
            "last_time_den",
            "last_time_vel",
            "last_time_pol",
            "vel_frame",
            "den_id",
            "vel_id",
            "vel_point_data",
            "vel_point_ids",
            "den_data",
            "vel_data",
            "pol_data",
            "time_den_arr",
            "time_vel_arr",
            "time_vel2_arr",
            "time_pol_arr",
        ])
        return v

    def collect(self) -> None:
        # time = self.solver.time
        time = self.solver.time
        time_dt = self.solver.num_time_steps

        if time < self.transient_time:
            return

        collect_vel = self.to_collect_vel(time_dt)
        collect_den = self.to_collect_den(time_dt)
        collect_pol = self.to_collect_pol(time_dt)
        
        if not collect_den and not collect_vel and not collect_pol:
            return

        num_active = self.solver.num_active_rings
        ids_active = np.array(self.solver.rings_ids[:num_active])
        cms = np.array(self.solver.center_mass)
        
        ids_in_region = None
        cms_in_region = None
        if collect_pol or collect_den or (collect_vel and self.vel_frame == 0):
            cms_active = cms[ids_active]
        
            mask_in_region = (cms_active[:, 0] > self.xlims[0]) & (cms_active[:, 0] < self.xlims[1])
            if mask_in_region.sum() == 0:
                return
        
            ids_in_region = ids_active[mask_in_region]
            cms_in_region = cms_active[mask_in_region]

        if collect_den:
            self.last_time_den = time_dt
            self.col_density(time, cms_in_region)

            if self.den_data.is_full:
                self.save_data(self.den_data, self.DataName.density)
                self.den_id += 1
                self.den_data.reset()
       
        if collect_pol:
            self.last_time_pol = time_dt
            self.col_polarity(time, ids_in_region.reshape(-1, 1))

            if self.pol_data.is_full:
                self.save_data(self.pol_data, self.DataName.polarity)
                self.pol_id += 1
                self.pol_data.reset()
                
        if collect_vel:
            if self.vel_frame == 0:
                self.last_time_vel = time_dt
            
            self.col_vel(time, ids_in_region, cms_in_region, cms)

            if self.vel_frame == 0:
                self.vel_frame = 1
            else:
                self.vel_frame = 0
            
            if self.vel_data.is_full:
                self.save_data(self.vel_data, self.DataName.velocity)
                self.vel_id += 1
                self.vel_data.reset()
        
        if self.autosave_cfg:
            self.check_autosave()

    def to_collect_vel(self, time_dt):
        if self.vel_dt is None:
            return False

        if self.vel_frame == 0:
            return time_dt - self.last_time_vel >= self.vel_dt

        return time_dt - self.last_time_vel >= self.vel_frame_dt

    def to_collect_pol(self, time_dt):
        if self.pol_dt is None:
            return False
        
        return time_dt - self.last_time_pol > self.pol_dt

    def to_collect_den(self, time_dt):
        if self.den_dt is None:
            return False
        
        return time_dt - self.last_time_den > self.den_dt

    def col_density(self, time, cms):
        self.time_den_arr.append(time)
        self.den_data.add(cms)

    def col_vel(self, time, ids_in_region, cms_in_region, cms):
        if self.vel_frame == 0:
            self.vel_point_ids = ids_in_region
            self.vel_point_data = np.empty((cms_in_region.shape[0], 4), dtype=self.vel_data.data.dtype)
            self.vel_point_data[:,:2] = cms_in_region
            self.time_vel_arr.append(time)
        else:
            self.vel_point_data[:,2:] = cms[self.vel_point_ids]
            self.time_vel2_arr.append(time)
            self.vel_data.add(self.vel_point_data)

    def col_polarity(self, time, ids_in_region):
        self.time_pol_arr.append(time)
        self.pol_data.add(self.solver.self_prop_angle[ids_in_region])

    def save_data(self, data: ArraySizeAware, name: DataName):
        if name is self.DataName.velocity:
            filename = f"vel_cms_{self.vel_id}"
        elif name is self.DataName.density:
            filename = f"den_cms_{self.den_id}"
        elif name is self.DataName.polarity:
            filename = f"pol_{self.pol_id}"
        
        file_path = self.data_path / (filename + ".pickle")
        with open(file_path, "wb") as f:
            pickle.dump(data, f)

    def save(self):
        while len(self.time_vel2_arr) != len(self.time_vel_arr):
            self.time_vel_arr.pop()

        vel_time_path = self.data_path / "vel_time.npy"
        vel2_time_path = self.data_path / "vel2_time.npy"
        den_time_path = self.data_path / "den_time.npy"
        pol_time_path = self.data_path / "pol_time.npy"
        np.save(vel_time_path, np.array(self.time_vel_arr))
        np.save(vel2_time_path, np.array(self.time_vel2_arr))
        np.save(den_time_path, np.array(self.time_den_arr))
        np.save(pol_time_path, np.array(self.time_pol_arr))
        
        # self.vel_data.strip()
        # self.den_data.strip()
        self.save_data(self.vel_data, self.DataName.velocity)
        self.save_data(self.den_data, self.DataName.density)
        self.save_data(self.pol_data, self.DataName.polarity)

        with open(self.data_path / "den_vel_metadata.yaml", "w") as f:
            yaml.dump({
                "density_eq": self.density_eq,
                "den_num_files": self.den_id+1,
                "vel_num_files": self.vel_id+1,
                "pol_num_files": self.pol_id+1,
                "num_data_points_per_file": self.num_data_points_per_file,
                "vel_frame_dt": self.vel_frame_dt * self.solver.dt,
            }, f)

Configs2Collector.add(DenVelColCfg, DenVelCol)