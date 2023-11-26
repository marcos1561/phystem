from tkinter import *
from tkinter import ttk
import threading, time
from typing import Type

from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from phystem.core.run_config import RealTimeCfg
from phystem.core.solvers import SolverCore
from phystem.utils.timer import TimeIt

from phystem.gui_phystem import control_ui, info_ui

class AppCore:
    def __init__(self, fig: Figure, cfgs: dict, solver: SolverCore, timer: TimeIt,
        run_cfg: RealTimeCfg, update_func, title: str=None,
        InfoT: Type[info_ui.InfoCore] = info_ui.InfoCore, 
        ControlT: Type[control_ui.ControlCore] = control_ui.ControlCore, 
        ) -> None:
        self.root = Tk()
        self.fig = fig
        self.update_func = update_func
        self.canvas: FigureCanvasTkAgg = None

        if title is not None:
            self.root.wm_title(title)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<<update_ui>>", self.update_ui)


        graph_frame = ttk.Frame(self.root)
        
        left_frame = ttk.Frame(self.root) 
        control_frame = ttk.Frame(left_frame)
        info_frame = ttk.Frame(left_frame)

        # self.info(info_frame) 
        # self.control(control_frame) 

        self.control = ControlT(control_frame, run_cfg)
        self.info = InfoT(info_frame, cfgs, solver, timer)
        
        self.control.configure_ui()
        self.info.configure_ui()
        self.graph(graph_frame) 
        
        left_frame.grid(row=0, column=0, pady=10, padx=20, sticky=(N, S, W, E))
        graph_frame.grid(row=0, column=1, sticky=(W, E, N, S))

        info_frame.grid(column=0, row=0, sticky=(N, S, W, E))
        control_frame.grid(column=0, row=1, sticky=(N, S, W, E), pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
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

    # def info(self, main_frame: ttk.Frame):
    #     f_main_frame = ttk.LabelFrame(main_frame, text="Info", padding=10, border=3)

    #     # s = self.get_info()
    #     # self.text = self.ax.text(0.01, 1-0.01, s,
    #     #     horizontalalignment='left',
    #     #     verticalalignment='top',
    #     #     transform=self.ax.transAxes)

    #     text = (
    #         "Nossa : d123\n"
    #         "Putz  : 120"
    #     )

    #     ttk.Label(f_main_frame, text=text).grid(column=0, row=0)

    #     f_main_frame.grid(sticky=(N, S, W, E))

    # def control(self, main_frame: ttk.Frame):
    #     f_main_frame = ttk.LabelFrame(main_frame, text="Control", padding=10, border=3)

    #     frequency = IntVar()

    #     vars = {"frequency": frequency}
    #     self.control_mng.vars = vars

    #     speed_frame = ttk.Frame(f_main_frame)
    #     speed_label = ttk.Label(speed_frame, text="Speed")        
    #     speed = ttk.Scale(speed_frame, from_=1, to=100, orient=HORIZONTAL,
    #                         command=self.control_mng.speed_callback, variable=frequency,
    #                         length=300)

    #     pause_btt = ttk.Button(f_main_frame, command=self.control_mng.pause_callback,
    #             text="Pausar")

    #     f_main_frame.grid(column=0, row=0, sticky=(W, E, N, S))
        
    #     pause_btt.grid(column=0, row=0)
        
    #     speed_frame.grid(column=0, row=1, sticky=W, pady=30)
    #     speed_label.grid(column=0, row=0)
    #     speed.grid(column=0, row=1, sticky=W)
        

    def update(self):
        fps = 60
        stop_time = 1/fps

        while True:
            time.sleep(stop_time)
            
            self.update_func()

            if self.to_run:
                self.root.event_generate("<<update_ui>>")
            else:
                return

    def update_ui(self, *args):
        self.canvas.draw()
        self.info.update()

    def run(self):
        self.to_run = True

        self.solver_thread = threading.Thread(target=self.update)
        self.solver_thread.start()

        self.root.mainloop()

    def on_closing(self):
        self.to_run = False
        self.solver_thread.join()
        self.root.destroy()