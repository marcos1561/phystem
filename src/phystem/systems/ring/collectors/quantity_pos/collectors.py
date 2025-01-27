from dataclasses import dataclass
import numpy as np

from .base import QuantityCfg, QuantityCol, QuantityState

class CmsCfg(QuantityCfg):
    "Configurações do coletor dos centros dos anéis."
    name = "cms"
    num_dims = 2

class CmsCol(QuantityCol):
    def collect(self, ids_in_region, cms_in_region):
        self.state.data.add(cms_in_region)


class VelocityCfg(QuantityCfg):
    name = "vel_cms"
    num_dims = 4
    def __init__(self, frame_dt: int):
        '''
        Configurações do coletor de velocidades dos anéis. 
        A dimensão dos pontos é 4 e a interpretação dos dados é a seguinte:
            
        collector.data[i] -> i-ésimo ponto. Array com dimensão (n_p, 4)
        collector.data[i, :, :2] -> Centros de massa na primeira coleta, digamos no tempo T = t.
        collector.data[i, :, 2:] -> Centros de massa na segunda coleta, no tempo T = t + `frame_dt`.

        Então, a velocidade de todos os pontos é dado por
        
        >>> (collector.data[:,:,2:] - collector.data[:,:,:2])/ (frame_dt * dt)

        Parâmetros:
        ----------
        frame_dt:
            Intervalo de tempo utilizado entre as coletas para calcular as velocidades
            em unidades de passos temporais.
        '''
        self.frame_dt = frame_dt

@dataclass
class VelState(QuantityState):
    vel_frame: int = 0
    vel_point_data: np.array = None
    vel_point_ids: np.array = None 

class VelocityCol(QuantityCol):
    configs: VelocityCfg
    state: VelState
    StateT = VelState

    def init_metadata(self, metadata):
        metadata["frame_dt"] = self.configs.frame_dt

    def before_save_metadata(self, metadata):
        metadata["last_point_completed"] = self.state.vel_frame == 0 

    def to_collect(self, time_dt: int, is_time: bool):
        if self.state.vel_frame == 0:
            return is_time

        return time_dt - self.root_state.col_last_time >= self.configs.frame_dt

    def collect(self, ids_in_region, cms_in_region):
        if self.state.vel_frame == 0:
            self.state.vel_point_ids = ids_in_region
            self.state.vel_point_data = np.empty((cms_in_region.shape[0], 4), dtype=self.state.data.data.dtype)
            self.state.vel_point_data[:,:2] = cms_in_region
        else:
            self.state.vel_point_data[:,2:] = self.solver.center_mass[self.state.vel_point_ids]
            self.state.data.add(self.state.vel_point_data)
        
        if self.state.vel_frame == 0:
            self.state.vel_frame = 1
        else:
            self.state.vel_frame = 0


class PolarityCfg(QuantityCfg):
    "Configurações do coletor do ângulo das polarizações."
    name = "pol"
    num_dims = 1

class PolarityCol(QuantityCol):
    def collect(self, ids_in_region, cms_in_region):
        self.data.add(self.solver.self_prop_angle[ids_in_region])


class AreaCfg(QuantityCfg):
    '''
    Configurações da coletor das áreas.
    
    OBS: A área coletada é a área do polígono formado pelos
        centros das partículas e não a área total dos anéis.
    '''
    name = "area"
    num_dims = 1

class AreaCol(QuantityCol):
    def collect(self, ids_in_region, cms_in_region):
        areas = np.array(self.solver.area_debug.area)[ids_in_region]
        self.data.add(areas)


quantity_cfg_to_col = {
    VelocityCfg: VelocityCol,
    CmsCfg: CmsCol,
    PolarityCfg: PolarityCol,
    AreaCfg: AreaCol,
}