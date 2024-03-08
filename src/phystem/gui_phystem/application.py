from tkinter import *
from tkinter import ttk
import threading, time
from typing import Type

from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from phystem.core.run_config import RealTimeCfg, UiSettings
from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt

from phystem.gui_phystem import control_ui, info_ui

class AppCore:
    def __init__(self, fig: Figure, cfgs: dict, solver: SolverCore, timer: TimeIt,
        run_cfg: RealTimeCfg, update_func, title: str=None,
        InfoT=info_ui.InfoCore, 
        ControlT=control_ui.ControlCore,
        ui_settings=UiSettings(), 
        ) -> None:
        self.root = Tk()
        self.fig = fig
        self.update_func = update_func
        self.canvas: FigureCanvasTkAgg = None
        self.run_cfg = run_cfg

        self.fig.set_dpi(ui_settings.dpi)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        scale = ui_settings.window_scale
        self.root.geometry(f"{int(screen_width*scale)}x{int(screen_height*scale)}")

        if title is not None:
            self.root.wm_title(title)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<<update_ui>>", self.update_ui)


        graph_frame = ttk.Frame(self.root)
        
        left_frame = ttk.Frame(self.root) 
        control_frame = ttk.Frame(left_frame)
        info_frame = ttk.Frame(left_frame)

        self.control = ControlT(control_frame, run_cfg, solver)
        self.info = InfoT(info_frame, cfgs, solver, timer)
        
        self.control.configure_ui()
        self.info.configure_ui()
        self.graph(graph_frame) 
        
        left_frame.grid(row=0, column=0, pady=10, padx=20, sticky=(N, S, W, E))
        graph_frame.grid(row=0, column=1, sticky=(W, E, N, S))

        info_frame.grid(column=0, row=0, sticky=(N, S, W, E))
        control_frame.grid(column=0, row=1, sticky=(N, S, W, E), pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=int(1/ui_settings.left_pannel_size))
        self.root.rowconfigure(0, weight=1)
        
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(0, weight=1)
        
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)

    def graph(self, main_frame: ttk.Frame):
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)  # A tk.DrawingArea.
        self.canvas.draw()

        toolbar = NavigationToolbar2Tk(self.canvas, main_frame, pack_toolbar=False)
        toolbar.update()

        self.canvas.mpl_connect(
            "key_press_event", lambda event: print(f"you pressed {event.key}"))
        self.canvas.mpl_connect("key_press_event", key_press_handler)

        self.canvas.get_tk_widget().grid(column=0, row=0, sticky=(W, E, N, S))
        toolbar.grid(column=0, row=1, sticky=W)

    def update(self):
        stop_time = 1/self.run_cfg.fps

        frame = 1
        while True:
            t1 = time.time()
            
            self.update_func(frame)
            frame += 1

            if self.to_run:
                self.root.event_generate("<<update_ui>>")
            else:
                return
            
            t2 = time.time()
            
            elapsed_time = t2 - t1
            wait_time = stop_time - elapsed_time
            if wait_time > 0:
                time.sleep(stop_time)
                elapsed_time += stop_time

            self.info.fps = 1/(elapsed_time)
            

    def update_ui(self, *args):
        # if not self.control.control_mng.is_paused:
        self.canvas.draw()
        
        self.info.update()

    def run(self):
        self.to_run = True

        self.solver_thread = threading.Thread(target=self.update, daemon=True)
        self.solver_thread.start()

        self.root.mainloop()

    def on_closing(self):
        self.to_run = False
        if self.solver_thread.is_alive():
            self.root.after(100, self.on_closing)
            return
        self.root.destroy()