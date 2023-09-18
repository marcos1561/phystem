'''
Coleção de pipelines de coleta de dados.

A assinatura de uma pipeline é a seguinte

func(sim, collect_cfg) -> None

Em que

sim: Simulation
    Referência os sistema que controla a simulação.

collect_cfg:
    Configurações utilizadas pela pipeline, que são informadas nas configurações
    do modo de execução de coleta de dados.
'''
from enum import Enum, auto

import phystem.self_propelling.collectors as collectors
from phystem.self_propelling.simulation import Simulation
from phystem.self_propelling.solvers import CppSolver
from phystem.self_propelling.configs import *
from phystem.self_propelling.run_config import CollectDataCfg

from ic_utils import progress

class CollectPlCfg:
    '''
    Configurações para a pipeline de coleta de dados.
    '''
    def __init__(self, only_last: bool) -> None:
        '''
        Parameters:
        -----------
            only_last:
                Se for `True` apenas coleta o último frame da simulação.
        '''
        self.only_last = only_last

def state(sim: Simulation, collect_cfg: CollectPlCfg):
    solver: CppSolver = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)
    if not collect_cfg.only_last:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            dt=run_cfg.dt, tf=run_cfg.tf, num_points=1000,
        )
        
        state_collector.collect(0)
        count = 0
        while solver.time < run_cfg.tf:
            solver.update()
            state_collector.collect(count)
            
            prog.update(solver.time)
            count += 1
        
        state_collector.save()
    else:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            tf=0, dt=run_cfg.dt, num_points=2,
        )
        
        state_collector.collect(0)
        while solver.time < run_cfg.tf:
            solver.update()
            prog.update(solver.time)
        
        state_collector.collect(0)
        state_collector.save()

def nabla_range(sim: Simulation, collect_cfg: CollectDataCfg):
    import numpy as np
    import os
    
    run_cfg: CollectDataCfg = sim.run_cfg
    solver: CppSolver = sim.solver

    num_points = 1000
    nabla_range = np.linspace(0, 3, 20)
    
    prog = progress.Continuos(nabla_range.max())
    
    mean_vel_data = np.zeros((nabla_range.size, num_points))
    for id, nabla in enumerate(nabla_range):
        sim.self_propelling_cfg.nabla = nabla
        sim.init_sim()

        collector = collectors.MeanVel(
            solver, run_cfg.tf, run_cfg.dt,
            num_points=num_points, path=run_cfg.folder_path,
        )

        count = 0
        while solver.time < run_cfg.tf:
            solver.update()
            collector.collect(count)
            count += 1
        
        prog.update(nabla)

        mean_vel_data[id] = collector.data[0]     
        time_data = collector.data[1]     
    
    folder_path = "data/self_propelling/nabla_0-01"
    np.save(os.path.join(folder_path, "mean_vel.npy"), mean_vel_data)
    np.save(os.path.join(folder_path, "nabla.npy"), nabla_range)
    np.save(os.path.join(folder_path, "time.npy"), time_data)

class FuncID(Enum):
    state = auto()
    nabla_range = auto()

def get_func(func_id: FuncID):
    func_mapping = {
        FuncID.state: state,
        FuncID.nabla_range: nabla_range,
    }
    return func_mapping[func_id]