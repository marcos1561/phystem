from tkinter import ttk
from tkinter import BooleanVar, W
from phystem.core.run_config import RealTimeCfg, RunType, ReplayDataCfg
from phystem.core.solvers import SolverCore

from phystem.systems.ring.solvers import CppSolver, SolverReplay
from phystem.systems.ring.configs import RingCfg, CreatorCfg
from phystem.systems.ring.ui.graph.graphs_cfg import *
from phystem.systems.ring.ui.graph import SimpleGraph

from phystem.gui_phystem.widgets import CbOption
from phystem.gui_phystem.info_ui import InfoCore
from phystem.gui_phystem.control_ui import ControlCore
from phystem.gui_phystem.control_mng import ControlManagerCore
from phystem.utils.timer import TimeIt

class ControlMng(ControlManagerCore):
    graph_cfg: SimpleGraphCfg
    solver: SolverCore
    main_graph: SimpleGraph

    def __init__(self, run_cfg: RealTimeCfg, solver: SolverCore, main_graph) -> None:
        super().__init__(run_cfg, solver, main_graph)
        if self.graph_cfg.begin_paused:
            self.is_paused = True

    def add_vars(self):
        # Components
        self.vars["show_circles"] = BooleanVar(value=self.graph_cfg.show_circles)
        self.vars["show_density"] = BooleanVar(value=self.graph_cfg.show_density)
        self.vars["show_scatter"] = BooleanVar(value=self.graph_cfg.show_scatter)
        self.vars["show_scatter_cont"] = BooleanVar(value=self.graph_cfg.show_scatter_cont)
        self.vars["show_springs"] = BooleanVar(value=self.graph_cfg.show_springs)
        self.vars["show_cms"] = BooleanVar(value=self.graph_cfg.show_cms)
        self.vars["show_invasion"] = BooleanVar(value=self.graph_cfg.show_invasion)
        self.vars["show_ith_points"] = BooleanVar(value=self.graph_cfg.show_ith_points)
        
        # Forces
        self.vars["show_f_springs"] = BooleanVar(value=self.graph_cfg.show_f_springs)
        self.vars["show_f_vol"] = BooleanVar(value=self.graph_cfg.show_f_vol)
        self.vars["show_f_area"] = BooleanVar(value=self.graph_cfg.show_f_area)
        self.vars["show_f_format"] = BooleanVar(value=self.graph_cfg.show_f_format)
        self.vars["show_f_obs"] = BooleanVar(value=self.graph_cfg.show_f_obs)
        self.vars["show_f_total"] = BooleanVar(value=self.graph_cfg.show_f_total)
        self.vars["show_f_invasion"] = BooleanVar(value=self.graph_cfg.show_f_invasion)

        # Other
        self.vars["circles_color"] = BooleanVar(value=self.graph_cfg.circles_cfg.color is None)
        self.vars["circles_facecolor"] = BooleanVar(value=self.graph_cfg.circles_cfg.facecolor)

    def show_component(self, name):
        setattr(self.graph_cfg, name, self.vars[name].get())

    def show_forces(self):
        self.graph_cfg.show_f_springs = self.vars["show_f_springs"].get()
        self.graph_cfg.show_f_vol = self.vars["show_f_vol"].get()
        self.graph_cfg.show_f_area = self.vars["show_f_area"].get()
        self.graph_cfg.show_f_total = self.vars["show_f_total"].get()
        self.graph_cfg.show_f_format = self.vars["show_f_format"].get()
        self.graph_cfg.show_f_obs = self.vars["show_f_obs"].get()
        self.graph_cfg.show_f_invasion = self.vars["show_f_invasion"].get()

    def circles_color(self):
        if self.vars["circles_color"].get():
            self.graph_cfg.circles_cfg.color = None
        else:
            self.graph_cfg.circles_cfg.color = "black"

    def circles_facecolor(self):
        self.graph_cfg.circles_cfg.facecolor = self.vars["circles_facecolor"].get()

class Control(ControlCore):
    control_mng: ControlMng

    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore, main_graph):
        return ControlMng(run_cfg, solver, main_graph)
    
    def configure_controls(self, main_frame: ttk.Frame):
        self.slider_lims = [1, 1000]

        show_frame = ttk.LabelFrame(main_frame, text="Components")
        show_widget = CbOption(show_frame, 5)
        for external_name, cfg_name in [
            ("Scatter", "show_scatter"),
            ("Circles", "show_circles"),
            ("Density", "show_density"),
            ("Springs", "show_springs"),
            ("Cms", "show_cms"),
            ("Invasion", "show_invasion"),
            ("Ith Points", "show_ith_points"),
        ]:
            show_widget.add(external_name, self.control_mng.vars[cfg_name],  lambda x=cfg_name: self.control_mng.show_component(x))
            
        forces_frame = ttk.LabelFrame(main_frame, text="Forces")
        forces_widget = CbOption(forces_frame, 4)
        for external_name, cfg_name in [
            ("Springs", "show_f_springs"),
            ("Vol", "show_f_vol"),
            ("Area", "show_f_area"),
            ("Format", "show_f_format"),
            ("Obs", "show_f_obs"),
            ("Invasion", "show_f_invasion"),
            ("Total", "show_f_total"),
        ]:
            forces_widget.add(external_name, self.control_mng.vars[cfg_name],  lambda x=cfg_name: self.control_mng.show_component(x))

        others_frame = ttk.LabelFrame(main_frame, text="Others")
        others_widget = CbOption(others_frame, 4)
        others_widget.add("Circles Color", self.control_mng.vars["circles_color"], self.control_mng.circles_color)
        others_widget.add("Circles Fc", self.control_mng.vars["circles_facecolor"], self.control_mng.circles_facecolor)

        # Control widgets grid
        show_widget.grid()
        forces_widget.grid()
        others_widget.grid()
        
        # Control widgets placement
        show_frame.grid(column=0, row=0, sticky="WE")
        forces_frame.grid(column=0, row=1, sticky="WE", pady=2)
        others_frame.grid(column=0, row=2, sticky="WE", pady=2)

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
    
    def get_control_mng(self, run_cfg: RealTimeCfg, solver: SolverCore, main_graph):
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