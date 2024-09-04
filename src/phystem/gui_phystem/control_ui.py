from tkinter import *
from tkinter import ttk

from typing import Type, Generic, TypeVar

from phystem.core.run_config import RealTimeCfg
from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt
from  . import widgets

from phystem.gui_phystem.control_mng import ControlManagerCore

class ControlCore():
    def __init__(self, main_frame: ttk.Frame, main_graph, run_cfg: RealTimeCfg, solver: SolverCore, slider_lims=[1, 100]) -> None:
        self.main_frame = main_frame
        self.control_mng = self.get_control_mng(run_cfg, solver, main_graph)

        self.slider_lims = slider_lims

    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore, main_graph):
        return ControlManagerCore(run_cfg, solver, main_graph)

    def configure_ui(self):
        label_frame = ttk.LabelFrame(self.main_frame, text="Control", padding=0, border=3)
        label_frame.columnconfigure(0, weight=1)

        base_frame = ttk.Frame(label_frame)
        self.configure_main(base_frame)

        controls_frame = ttk.Frame(label_frame)
        self.configure_controls(controls_frame)

        label_frame.grid(column=0, row=0, sticky=(W, E, N, S))
        base_frame.grid(column=0, row=0, sticky=(W, E, N, S), pady=10, padx=10)
        controls_frame.grid(column=0, row=1, sticky=(W, E, N, S), padx=10)

        base_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(0, weight=1)
        # controls_frame.columnconfigure(1, weight=1)

    def configure_main(self, main_frame: ttk.Frame):
        # pause_btt = ttk.Button(main_frame, command=self.control_mng.pause_callback,
        #         text="Pausar", width=20)
        state = widgets.PlayButton.State.running
        if self.control_mng.is_paused:
            state = widgets.PlayButton.State.stopped

        play_bttn = widgets.PlayButton(main_frame, init_state=state, width=20,
            callback=self.control_mng.pause_callback,
        )
        self.play_bttn = play_bttn

        speed_var = self.control_mng.vars["frequency"]
        speed_frame = ttk.Frame(main_frame)
        speed_label = ttk.Label(speed_frame, text="Speed")        
        speed_slider = ttk.Scale(speed_frame, from_=self.slider_lims[0], to=self.slider_lims[1], orient=HORIZONTAL,
                        command=self.control_mng.speed_callback, variable=speed_var,
                        length=150)

        advance_button = ttk.Button(main_frame, command=self.control_mng.advance_once_callback,
            text="Próximo Frame", width=20)

        div = ttk.Separator(main_frame)

        play_bttn.grid(column=0, row=0, sticky="WS")

        speed_frame.grid(column=1, row=0, sticky="WE", padx=10)
        speed_label.grid(column=0, row=0)
        speed_slider.grid(column=0, row=1, sticky="WE")

        advance_button.grid(column=0, row=1, columnspan=2, pady=10, sticky="WE")

        div.grid(column=0, row=2, columnspan=2, sticky="WE")

        speed_frame.columnconfigure(0, weight=1)

    def set_is_paused(self, value):
        if value != self.control_mng.is_paused:
            self.play_bttn.on_click()

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