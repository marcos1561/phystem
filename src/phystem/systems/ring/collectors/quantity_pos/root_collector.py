import numpy as np

from phystem.systems.ring.collectors import RingCol
from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.run_config import RingCfg
from phystem.systems.ring.configs import SpaceCfg

from .base import QuantityPosState, QuantityPosCfg, QuantityCol
from .collectors import CmsCfg, quantity_cfg_to_col

class QuantityPosCol(RingCol):
    solver: CppSolver

    def __init__(self, col_cfg: QuantityPosCfg, solver: CppSolver, root_path, configs, 
        exist_ok=False, **kwargs):
        '''
        Gerenciador de coletores de quantidades associadas às posições dos anéis.
        Para mais informações ver doc de `QuantityPosCfg`.
        '''
        super().__init__(solver, root_path, configs, col_cfg.autosave_cfg, exist_ok, **kwargs)
        self.col_cfg = col_cfg
        
        has_cms_cfg = False
        for q in self.col_cfg.quantities_cfg:
            if type(q) is CmsCfg:
                has_cms_cfg = True
                break
        
        if not has_cms_cfg:
            self.col_cfg.quantities_cfg.append(CmsCfg())

        dynamic_cfg: RingCfg = configs["dynamic_cfg"]
        space_cfg: SpaceCfg = configs["space_cfg"]
        
        area_eq = dynamic_cfg.get_equilibrium_area()
        
        xlims, ylims = col_cfg.xlims, col_cfg.ylims
        l = xlims[1] - xlims[0]
        h = ylims[1] - ylims[0]
        
        if l > space_cfg.length:
            l = space_cfg.length
        if h > space_cfg.height:
            h = space_cfg.height
        
        num_max_rings = int(l * h / area_eq * 1.2)
        
        self.state = QuantityPosState(self.solver.num_time_steps)
        
        self.quantities: list[QuantityCol] = [
            quantity_cfg_to_col[type(q_cfg)](q_cfg, self.state, self.col_cfg, self.solver, num_max_rings, self.data_path)
            for q_cfg in self.col_cfg.quantities_cfg
        ]

        self.quantities_states = [q.state for q in self.quantities]
        
    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend([ 
            "state",
            "quantities_states",
        ])
        return v
    
    @staticmethod
    def get_kwargs_configs(cfg: QuantityPosCfg):
        if type(cfg) is not QuantityPosCfg:
            raise ValueError(f"A configuração deve ser do tipo `QuantityPosCfg`, mas seu tipo é {type(cfg)}.")

        return {"col_cfg": cfg}

    def get_is_time(self):
        '''
        Retorna `True` se o tempo decorrido desde a última coleta é
        maior do que o intervalo de tempo entre coletas.
        '''
        return self.solver.num_time_steps - self.state.col_last_time >= self.col_cfg.collect_dt

    def cms_in_region(self):
        '''
        Retorna as posições dos anéis e seus ids na lista
        global de anéis que estão dentro da região de coleta.
        '''
        num_active = self.solver.num_active_rings
        ids_active = self.solver.rings_ids[:num_active]
        cms = self.solver.center_mass
        
        cms_active = cms[ids_active]
        
        if self.col_cfg.check_type is not self.col_cfg.CheckType.none:
            if self.col_cfg.check_type is self.col_cfg.CheckType.only_x:
                mask_in_region = self.mask_x_region(cms_active)
            elif self.col_cfg.check_type is self.col_cfg.CheckType.only_y:
                mask_in_region = self.mask_y_region(cms_active)
            else:
                mask_in_region = self.mask_y_region(cms_active) & self.mask_x_region(cms_active)

            ids_in_region = ids_active[mask_in_region]
            cms_in_region = cms_active[mask_in_region]
        else:
            ids_in_region = ids_active
            cms_in_region = cms_active

        return ids_in_region, cms_in_region

    def mask_x_region(self, cms_active):
        return (cms_active[:, 0] > self.col_cfg.xlims[0]) & (cms_active[:, 0] < self.col_cfg.xlims[1])

    def mask_y_region(self, cms_active):
        return (cms_active[:, 1] > self.col_cfg.ylims[0]) & (cms_active[:, 1] < self.col_cfg.ylims[1])

    def collect(self):
        time_dt = self.solver.num_time_steps
        is_time = self.get_is_time()

        ids_in_region, cms_in_region = None, None
        if is_time:
            ids_in_region, cms_in_region = self.cms_in_region() 

        for q in self.quantities:
            if q.to_collect(time_dt, is_time):
                q.collect(ids_in_region, cms_in_region)
        
            if q.state.data.is_full:
                q.save_data()
                q.state.file_id += 1
                q.state.data.reset()

        if is_time:
            self.state.times.append(self.solver.time)
            self.state.col_last_time = time_dt

        if self.autosave_cfg:
            self.check_autosave()

    def save(self):
        for q in self.quantities:
            q.save()

        np.save(self.data_path / "times.npy", np.array(self.state.times))

    def load_autosave(self, use_backup=False):
        r = super().load_autosave(use_backup)
        
        for q, s in zip(self.quantities, self.quantities_states):
            q.state = s

        return r

