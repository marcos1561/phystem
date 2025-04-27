
from tkinter import StringVar, IntVar

from phystem.core.run_config import RealTimeCfg
from phystem.core.solvers import SolverCore

class ControlManagerCore:
    '''
    Controla a funcionalidade dos widgets.
    '''
    def __init__(self, run_cfg: RealTimeCfg, solver: SolverCore, main_graph=None) -> None:
        self.run_cfg = run_cfg
        self.graph_cfg = run_cfg.graph_cfg
        self.solver = solver
        self.main_graph = main_graph
        self.vars = {
            "frequency": IntVar(value=run_cfg.num_steps_frame),
        } 
        self.add_vars()

        self.is_paused = False
        self.advance_once = False
    
    def add_vars(self):
        pass

    def advance_once_callback(self):
        self.advance_once = True

    def pause_callback(self):
        if self.is_paused:
            self.is_paused = False
        else:
            self.is_paused = True
   
    def speed_callback(self, val):
        self.run_cfg.num_steps_frame = self.vars["frequency"].get()