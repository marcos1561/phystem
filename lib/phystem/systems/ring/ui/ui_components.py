from tkinter import ttk
from tkinter import BooleanVar, W
from phystem.core.run_config import RealTimeCfg

from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.configs import RingCfg, CreatorCfg
from phystem.systems.ring.ui.graph import GraphCfg

from phystem.gui_phystem.info_ui import InfoCore
from phystem.gui_phystem.control_ui import ControlCore
from phystem.gui_phystem.control_mng import ControlManagerCore
from phystem.utils.timer import TimeIt

class ControlMng(ControlManagerCore):
    graph_cfg: GraphCfg
    
    def __init__(self, run_cfg: RealTimeCfg) -> None:
        super().__init__(run_cfg)

        if self.graph_cfg.begin_paused:
            self.is_paused = True

    def add_vars(self):
        self.vars["show_circles"] = BooleanVar(value=self.graph_cfg.show_circles)
        self.vars["f_springs"] = BooleanVar(value=self.graph_cfg.show_f_spring)
        self.vars["f_vol"] = BooleanVar(value=self.graph_cfg.show_f_vol)
        self.vars["f_area"] = BooleanVar(value=self.graph_cfg.show_f_area)
        self.vars["f_total"] = BooleanVar(value=self.graph_cfg.show_f_total)
        self.vars["pos_cont"] = BooleanVar(value=self.graph_cfg.show_pos_cont)

    def show_circles(self):
        self.graph_cfg.show_circles = self.vars["show_circles"].get()

    def show_forces(self):
        self.graph_cfg.show_f_spring = self.vars["f_springs"].get()
        self.graph_cfg.show_f_vol = self.vars["f_vol"].get()
        self.graph_cfg.show_f_area = self.vars["f_area"].get()
        self.graph_cfg.show_f_total = self.vars["f_total"].get()
    
    def show_pos_cont(self):
        self.graph_cfg.show_pos_cont = self.vars["pos_cont"].get()

class Control(ControlCore):
    control_mng: ControlMng

    def get_control_mng(self, run_cfg: RealTimeCfg) -> ControlMng:
        return ControlMng(run_cfg)

    def configure_ui(self):
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

        show_circles.grid(column=0, row=2, sticky=W)
        
        forces_frame.grid(column=0, row=3, pady=15, sticky=W)
        for id, f_cb in enumerate(forces_cb):
            f_cb.grid(column=id, row=0, padx=10)

        pos_cont.grid(column=0, row=4, pady=15, sticky=W)


class Info(InfoCore):
    solver: CppSolver

    def __init__(self, main_frame: ttk.Frame, cfgs: dict, solver: CppSolver, timer: TimeIt) -> None:
        super().__init__(main_frame, cfgs, solver, timer)

        dynamic_cfg: RingCfg = self.cfgs["dynamic_cfg"]
        creator_cfg: CreatorCfg = self.cfgs["creator_cfg"]
        self.cfg_info = dynamic_cfg.info() + f"N = {creator_cfg.num_p}\n" 

    def get_info(self) -> str:
        return (
            f"Delta T (ms): {self.timer.mean_time():.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.5f}\n"
            f"Area = {self.solver.cpp_solver.area_debug.area[0]:.3f}\n"
            "\n"
            f"spring_overlap: {self.solver.spring_debug.count_overlap}\n"
            f"vol_overlap   : {self.solver.excluded_vol_debug.count_overlap}\n"
            f"area_overlap  : {self.solver.area_debug.count_overlap}\n"
            f"zero_speed    : {self.solver.update_debug.count_zero_speed}\n"
            "\n"
            f"{self.cfg_info}"
        )