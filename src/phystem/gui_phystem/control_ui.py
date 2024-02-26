from tkinter import *
from tkinter import ttk

from typing import Type, Generic, TypeVar

from phystem.core.run_config import RealTimeCfg
from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt

from phystem.gui_phystem.control_mng import ControlManagerCore

class ControlCore():
    def __init__(self, main_frame: ttk.Frame, run_cfg: RealTimeCfg, slider_lims=[1, 100]) -> None:
        self.main_frame = main_frame
        self.control_mng = self.get_control_mng(run_cfg)

        self.slider_lims = slider_lims

    def get_control_mng(self, run_cfg: RealTimeCfg):
        return ControlManagerCore(run_cfg)

    def configure_ui(self):
        f_main_frame = ttk.LabelFrame(self.main_frame, text="Control", padding=10, border=3)

        frequency = self.control_mng.vars["frequency"]
        speed_frame = ttk.Frame(f_main_frame)
        speed_label = ttk.Label(speed_frame, text="Speed")        
        speed = ttk.Scale(speed_frame, from_=self.slider_lims[0], to=self.slider_lims[1], orient=HORIZONTAL,
                            command=self.control_mng.speed_callback, variable=frequency,
                            length=300)

        pause_btt = ttk.Button(f_main_frame, command=self.control_mng.pause_callback,
                text="Pausar", width=20)

        f_main_frame.grid(column=0, row=0, sticky=(W, E, N, S))
        
        pause_btt.grid(column=0, row=0, sticky=W)
        
        speed_frame.grid(column=0, row=1, sticky=W, pady=30)
        speed_label.grid(column=0, row=0)
        speed.grid(column=0, row=1, sticky=W)

        return f_main_frame


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