from phystem.systems.ring.simulation import Simulation
from phystem.core.solvers import SolverCore
from phystem.systems.ring import collectors

from phystem.core.run_config import CollectDataCfg 

from phystem.utils import progress


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

class CheckPointCfg:
    '''
    Configurações para a pipeline de coleta de dados.
    '''
    def __init__(self, num_checkpoints: int) -> None:
        self.num_checkpoints = num_checkpoints

def state(sim: Simulation, collect_cfg: CollectPlCfg):
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)
    if not collect_cfg.only_last:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            dt=run_cfg.int_cfg.dt, tf=run_cfg.tf, num_points=1000,
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
            tf=0, dt=run_cfg.int_cfg.dt, num_points=2,
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
        tf=run_cfg.tf, dt=run_cfg.int_cfg.dt, num_points=1000,
    )
    
    count = 1
    while solver.time < run_cfg.tf:
        solver.update()
        area_collector.collect(count)
        
        prog.update(solver.time)
        count += 1
    
    area_collector.save()

def last_state(sim: Simulation, collect_cfg):
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)

    collector = collectors.LastState(solver, run_cfg.folder_path, sim.configs)

    while solver.time < run_cfg.tf:
        solver.update()
        prog.update(solver.time)
    
    collector.save()

def checkpoints(sim: Simulation, collect_cfg: CheckPointCfg):
    solver: SolverCore = sim.solver
    run_cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(run_cfg.tf)

    collector = collectors.StateCheckpoint(solver, run_cfg.folder_path, sim.configs,
        num_checkpoints=collect_cfg.num_checkpoints, tf=run_cfg.tf)

    count = 1
    while solver.time < run_cfg.tf:
        solver.update()
        collector.collect(count)
        prog.update(solver.time)
        count += 1
    
    print("num saves:", collector.num_saves)

from enum import Enum, auto
class FuncID(Enum):
    last_pos = auto()

def get_func(func_id: FuncID):
    func_mapping = {
        FuncID.last_pos: last_state,
    }
    return func_mapping[func_id]