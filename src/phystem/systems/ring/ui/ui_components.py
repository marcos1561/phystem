from tkinter import ttk
from tkinter import BooleanVar, W
from phystem.core.run_config import RealTimeCfg, RunType, ReplayDataCfg
from phystem.core.solvers import SolverCore

from phystem.systems.ring.solvers import CppSolver, SolverReplay
from phystem.systems.ring.configs import RingCfg, CreatorCfg
from phystem.systems.ring.ui.graphs_cfg import *

from phystem.gui_phystem.info_ui import InfoCore
from phystem.gui_phystem.control_ui import ControlCore
from phystem.gui_phystem.control_mng import ControlManagerCore
from phystem.utils.timer import TimeIt

class ControlMng(ControlManagerCore):
    graph_cfg: MainGraphCfg
    solver: SolverCore

    def __init__(self, run_cfg: RealTimeCfg, solver: SolverCore) -> None:
        super().__init__(run_cfg, solver)
        if self.graph_cfg.begin_paused:
            self.is_paused = True

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

    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore):
        return ControlMng(run_cfg, solver)
    
    def configure_controls(self, main_frame: ttk.Frame):
        self.slider_lims = [1, 1000]
    
        show_circles = ttk.Checkbutton(main_frame, command=self.control_mng.show_circles,
            text="Show circles", variable=self.control_mng.vars["show_circles"])

        forces_frame = ttk.Frame(main_frame)
        f_springs = ttk.Checkbutton(forces_frame, text="Springs", 
            variable=self.control_mng.vars["f_springs"], command=self.control_mng.show_forces)
        f_vol = ttk.Checkbutton(forces_frame, text="Vol", 
            variable=self.control_mng.vars["f_vol"], command=self.control_mng.show_forces)
        f_area = ttk.Checkbutton(forces_frame, text="Area", 
            variable=self.control_mng.vars["f_area"], command=self.control_mng.show_forces)
        f_total = ttk.Checkbutton(forces_frame, text="Total", 
            variable=self.control_mng.vars["f_total"], command=self.control_mng.show_forces)
        forces_cb = [f_springs, f_vol, f_area, f_total]
    
        pos_cont = ttk.Checkbutton(main_frame, text="Pos Cont", 
            variable=self.control_mng.vars["pos_cont"], command=self.control_mng.show_pos_cont)
        
        
        cb_frame = ttk.Frame(main_frame)

        center_mass = ttk.Checkbutton(cb_frame, text="Center Mass", 
            variable=self.control_mng.vars["center_mass"], command=self.control_mng.show_center_mass)
        
        inside_points = ttk.Checkbutton(cb_frame, text="Inside Points", 
            variable=self.control_mng.vars["inside_points"], command=self.control_mng.show_inside_points)
        
        advance_button = ttk.Button(main_frame, command=self.control_mng.advance_once_callback,
            text="Próximo Frame", width=20)

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
        if self.cfgs["run_cfg"].id is RunType.REPLAY_DATA:
            return (
                f"fps: {self.fps:.1f}\n"
                f"Solver Delta T (ms): {self.timer.mean_time('solver'):.3f}\n"
                f"Graph  Delta T (ms): {self.timer.mean_time('graph'):.3f}\n\n"
                f"t : {self.solver.time:.3f}\n"
                f"dt: {self.solver.dt:.5f}\n"
                "\n"
                f"{self.cfg_info}"
            )

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


class ControlMngReplay(ControlManagerCore):
    graph_cfg: ReplayGraphCfg
    solver: SolverReplay
    run_cfg: ReplayDataCfg

    def __init__(self, run_cfg: RealTimeCfg, solver: SolverCore) -> None:
        super().__init__(run_cfg, solver)

        if self.graph_cfg.begin_paused:
            self.is_paused = True

    def change_time_callback(self):
        self.solver.time_sign *= -1
    
class ControlReplay(ControlCore):
    control_mng: ControlMngReplay
    
    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore):
        return ControlMngReplay(run_cfg, solver)

    def configure_controls(self, main_frame: ttk.Frame):
        change_time_button = ttk.Button(main_frame, command=self.control_mng.change_time_callback,
            text="Reverter Tempo", width=20)
        
        change_time_button.grid(column=0, row=7, sticky=W, pady=15)

class InfoReplay(InfoCore):
    solver: SolverReplay

    def __init__(self, main_frame: ttk.Frame, cfgs: dict, solver: SolverCore, timer: TimeIt) -> None:
        super().__init__(main_frame, cfgs, solver, timer)

        dynamic_cfg: RingCfg = self.cfgs["dynamic_cfg"]
        creator_cfg: CreatorCfg = self.cfgs["creator_cfg"]
        self.cfg_info = dynamic_cfg.info() + f"N = {creator_cfg.num_p}\n" 

    def get_info(self) -> str:
        return (
            f"fps: {self.fps:.1f}\n"
            f"Solver Delta T (ms): {self.timer.mean_time('solver'):<8.3f}\n"
            f"Graph  Delta T (ms): {self.timer.mean_time('graph'):<8.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.5f}\n"
            "\n"
            f"{self.cfg_info}"
        )