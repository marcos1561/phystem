from tkinter import ttk
from tkinter import BooleanVar, W
from tkinter.ttk import Frame
from phystem.core.run_config import RealTimeCfg

from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.configs import RingCfg, CreatorCfg
from phystem.systems.ring.ui.graphs_cfg import *

from phystem.gui_phystem.info_ui import InfoCore
from phystem.gui_phystem.control_ui import ControlCore
from phystem.gui_phystem.control_mng import ControlManagerCore
from phystem.utils.timer import TimeIt

class ControlMng(ControlManagerCore):
    graph_cfg: MainGraphCfg
    
    def __init__(self, run_cfg: RealTimeCfg) -> None:
        super().__init__(run_cfg)
        if self.graph_cfg.begin_paused:
            self.is_paused = True

        self.advance_once = False

    def add_vars(self):
        if type(self.graph_cfg) != MainGraphCfg:
            self.graph_cfg = MainGraphCfg(
                begin_paused=self.graph_cfg.begin_paused)
        
        self.vars["show_circles"] = BooleanVar(value=self.graph_cfg.show_circles)
        self.vars["f_springs"] = BooleanVar(value=self.graph_cfg.show_f_spring)
        self.vars["f_vol"] = BooleanVar(value=self.graph_cfg.show_f_vol)
        self.vars["f_area"] = BooleanVar(value=self.graph_cfg.show_f_area)
        self.vars["f_total"] = BooleanVar(value=self.graph_cfg.show_f_total)
        self.vars["pos_cont"] = BooleanVar(value=self.graph_cfg.show_pos_cont)
        self.vars["center_mass"] = BooleanVar(value=self.graph_cfg.show_center_mass)
        self.vars["inside_points"] = BooleanVar(value=self.graph_cfg.show_inside)

    def advance_once_callback(self):
        self.advance_once = True

    def show_circles(self):
        self.graph_cfg.show_circles = self.vars["show_circles"].get()

    def show_forces(self):
        self.graph_cfg.show_f_spring = self.vars["f_springs"].get()
        self.graph_cfg.show_f_vol = self.vars["f_vol"].get()
        self.graph_cfg.show_f_area = self.vars["f_area"].get()
        self.graph_cfg.show_f_total = self.vars["f_total"].get()
    
    def show_pos_cont(self):
        self.graph_cfg.show_pos_cont = self.vars["pos_cont"].get()
    
    def show_center_mass(self):
        self.graph_cfg.show_center_mass = self.vars["center_mass"].get()
    
    def show_inside_points(self):
        self.graph_cfg.show_inside = self.vars["inside_points"].get()

class Control(ControlCore):
    control_mng: ControlMng

    def get_control_mng(self, run_cfg: RealTimeCfg):
        return ControlMng(run_cfg)

    def configure_ui(self):
        self.slider_lims = [1, 1000]
        f_main_frame = super().configure_ui()
    
        show_circles = ttk.Checkbutton(f_main_frame, command=self.control_mng.show_circles,
            text="Show circles", variable=self.control_mng.vars["show_circles"])

        forces_frame = ttk.Frame(f_main_frame)
        f_springs = ttk.Checkbutton(forces_frame, text="Springs", 
            variable=self.control_mng.vars["f_springs"], command=self.control_mng.show_forces)
        f_vol = ttk.Checkbutton(forces_frame, text="Vol", 
            variable=self.control_mng.vars["f_vol"], command=self.control_mng.show_forces)
        f_area = ttk.Checkbutton(forces_frame, text="Area", 
            variable=self.control_mng.vars["f_area"], command=self.control_mng.show_forces)
        f_total = ttk.Checkbutton(forces_frame, text="Total", 
            variable=self.control_mng.vars["f_total"], command=self.control_mng.show_forces)
        forces_cb = [f_springs, f_vol, f_area, f_total]
    
        pos_cont = ttk.Checkbutton(f_main_frame, text="Pos Cont", 
            variable=self.control_mng.vars["pos_cont"], command=self.control_mng.show_pos_cont)
        
        
        cb_frame = ttk.Frame(f_main_frame)

        center_mass = ttk.Checkbutton(cb_frame, text="Center Mass", 
            variable=self.control_mng.vars["center_mass"], command=self.control_mng.show_center_mass)
        
        inside_points = ttk.Checkbutton(cb_frame, text="Inside Points", 
            variable=self.control_mng.vars["inside_points"], command=self.control_mng.show_inside_points)
        
        advance_button = ttk.Button(f_main_frame, command=self.control_mng.advance_once_callback,
            text="Avançar", width=20)

        show_circles.grid(column=0, row=2, sticky=W)
        
        forces_frame.grid(column=0, row=3, pady=15, sticky=W)
        for id, f_cb in enumerate(forces_cb):
            f_cb.grid(column=id, row=0, padx=10)

        pos_cont.grid(column=0, row=4, pady=15, sticky=W)
        
        cb_frame.grid(column=0, row=5, sticky=W, pady=15)
        center_mass.grid(column=0, row=0)
        inside_points.grid(column=1, row=0, padx=10)
        
        advance_button.grid(column=0, row=6, sticky=W, pady=15)


class Info(InfoCore):
    solver: CppSolver

    def __init__(self, main_frame: ttk.Frame, cfgs: dict, solver: CppSolver, timer: TimeIt) -> None:
        super().__init__(main_frame, cfgs, solver, timer)

        dynamic_cfg: RingCfg = self.cfgs["dynamic_cfg"]
        creator_cfg: CreatorCfg = self.cfgs["creator_cfg"]
        self.cfg_info = dynamic_cfg.info() + f"N = {creator_cfg.num_p}\n" 

    def get_info(self) -> str:
        if self.cfgs["run_cfg"].graph_cfg.cpp_is_debug:
            return (
                f"fps: {self.fps:.1f}\n"
                f"Solver Delta T (ms): {self.timer.mean_time('solver'):.3f}\n"
                f"Graph  Delta T (ms): {self.timer.mean_time('graph'):.3f}\n\n"
                f"t : {self.solver.time:.3f}\n"
                f"dt: {self.solver.dt:.5f}\n"
                "\n"
                f"num_active: {self.solver.num_active_rings}\n"
                f"area = {self.solver.cpp_solver.area_debug.area[0]:.3f}\n"
                f"intersect     : {self.solver.cpp_solver.in_pol_checker.num_inside_points}\n"
                "\n"
                f"{self.cfg_info}"
            )
        else:
            return (
                f"fps: {self.fps:.1f}\n"
                f"Delta T (ms): {self.timer.mean_time():.3f}\n\n"
                f"t : {self.solver.time:.3f}\n"
                f"dt: {self.solver.dt:.5f}\n"
                "\n"
                f"num_active: {self.solver.num_active_rings}\n"
                f"intersect     : {self.solver.cpp_solver.in_pol_checker.num_inside_points}\n"
                "\n"
                f"{self.cfg_info}"
            )