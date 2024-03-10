from tkinter import *
from tkinter import ttk

from typing import Type, Generic, TypeVar

from phystem.core.run_config import RealTimeCfg
from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt

from phystem.gui_phystem.control_mng import ControlManagerCore

class ControlCore():
    def __init__(self, main_frame: ttk.Frame, run_cfg: RealTimeCfg, solver: SolverCore, slider_lims=[1, 100]) -> None:
        self.main_frame = main_frame
        self.control_mng = self.get_control_mng(run_cfg, solver)

        self.slider_lims = slider_lims

    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore):
        return ControlManagerCore(run_cfg, solver)

    def configure_ui(self):
        label_frame = ttk.LabelFrame(self.main_frame, text="Control", padding=10, border=3)
        
        base_frame = ttk.Frame(label_frame)
        self.configure_main(base_frame)

        controls_frame = ttk.Frame(label_frame)
        self.configure_controls(controls_frame)

        label_frame.grid(column=0, row=0, sticky=(W, E, N, S))
        base_frame.grid(column=0, row=0, sticky=(W, E, N, S))
        controls_frame.grid(column=0, row=1, sticky=(W, E, N, S))

    def configure_main(self, main_frame: ttk.Frame):
        pause_btt = ttk.Button(main_frame, command=self.control_mng.pause_callback,
                text="Pausar", width=20)
        
        speed_var = self.control_mng.vars["frequency"]
        speed_frame = ttk.Frame(main_frame)
        speed_label = ttk.Label(speed_frame, text="Speed")        
        speed_slider = ttk.Scale(speed_frame, from_=self.slider_lims[0], to=self.slider_lims[1], orient=HORIZONTAL,
                        command=self.control_mng.speed_callback, variable=speed_var,
                        length=300)
        # speed_value = ttk.Entry(speed_frame, textvariable=speed_var, width=5)

        pause_btt.grid(column=0, row=0, sticky=W)

        speed_frame.grid(column=0, row=2, sticky=W, pady=15)
        speed_label.grid(column=0, row=0)
        speed_slider.grid(column=0, row=1, sticky=W)
        # speed_value.grid(column=1, row=1, padx=10)

    def configure_controls(self, main_frame: ttk.Frame):
        pass

if __name__ == "__main__":
    class S:
        def __init__(self) -> None:
            self.c= 0

    class SA(S):
        def __init__(self) -> None:
            self.a = 1
    
    class S2(S):
        def __init__(self) -> None:
            self.b = 2

    SystemT = TypeVar("SystemT", bound=S)
    class App():
        def __init__(self, SystemT: Type[S]) -> None:
            self.system = SystemT()

    app = App(SA)