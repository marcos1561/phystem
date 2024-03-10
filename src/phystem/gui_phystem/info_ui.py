from tkinter import *
from tkinter import ttk

from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt

class InfoCore:
    def __init__(self, main_frame: ttk.Frame, cfgs: dict, solver: SolverCore, timer: TimeIt) -> None:
        self.main_frame = main_frame
        
        self.fps = 0

        self.cfgs = cfgs
        self.solver = solver
        self.timer = timer

        self.text_var = StringVar()
    
    def get_info(self) -> str:
        return (
            f"fps    : {self.fps:.3f}\n"
            f"Solver Delta T (ms): {self.timer.mean_time('solver'):.3f}\n"
            f"Graph  Delta T (ms): {self.timer.mean_time('graph'):.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.5f}\n"
        )

    def configure_ui(self):
        f_main_frame = ttk.LabelFrame(self.main_frame, text="Info", padding=10, border=3)

        self.text_var.set(self.get_info())
        ttk.Label(f_main_frame, textvariable=self.text_var).grid(column=0, row=0)

        f_main_frame.grid(sticky=(N, S, W, E))

    def update(self):
        self.text_var.set(self.get_info())
