from phystem.core.solvers import SolverCore
from phystem.ring.run_config import CollectDataCfg 

from phystem.ring.simulation import Simulation
from phystem.ring import collectors

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
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)
    if not collect_cfg.only_last:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            dt=run_cfg.dt, tf=run_cfg.tf, num_points=1000,
        )
        
        state_collector.collect(0)
        count = 1
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

def area(sim: Simulation, collect_cfg: CollectPlCfg):
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)
    area_collector = collectors.AreaCollector(
        solver, run_cfg.folder_path, sim.configs,
        tf=run_cfg.tf, dt=run_cfg.dt, num_points=1000,
    )
    
    count = 1
    while solver.time < run_cfg.tf:
        solver.update()
        area_collector.collect(count)
        
        prog.update(solver.time)
        count += 1
    
    area_collector.save()

def last_pos(sim: Simulation, collect_cfg):
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)

    collector = collectors.LastPos(solver, run_cfg.folder_path, sim.configs)

    while solver.time < run_cfg.tf:
        solver.update()
        prog.update(solver.time)
    
    collector.save()

from enum import Enum, auto
class FuncID(Enum):
    last_pos = auto()

def get_func(func_id: FuncID):
    func_mapping = {
        FuncID.last_pos: last_pos,
    }
    return func_mapping[func_id]