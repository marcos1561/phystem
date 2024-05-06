from matplotlib.figure import Figure

from phystem.core.simulation import SimulationCore
from phystem.core.solvers import SolverCore
from phystem.systems.ring.solvers import CppSolver, SolverRD, SolverReplay
from phystem.systems.ring.creators import CreatorRD, Creator

from phystem.core.run_config import RunCfg, RunType, RealTimeCfg, ReplayDataCfg
from phystem.systems.ring.configs import CreatorCfg, RingCfg, InvaginationCfg, InvaginationCreatorCfg
from phystem.systems.ring.run_config import IntegrationCfg, UpdateType

from phystem.systems.ring.ui import graph_type, graphs_cfg
from phystem.systems.ring.ui import ui_components


from phystem.gui_phystem.mpl.widget import WidgetType
from phystem.gui_phystem.application import AppCore

class Simulation(SimulationCore):
    solver: CppSolver
    creator_cfg: CreatorCfg
    dynamic_cfg: RingCfg

    def __init__(self, creator_cfg: CreatorCfg, dynamic_cfg: RingCfg, space_cfg, run_cfg: RunCfg, other_cfgs: dict = None, rng_seed: float = None) -> None:
        int_cfg: IntegrationCfg = run_cfg.int_cfg
        if int_cfg.update_type is UpdateType.INVAGINATION and type(creator_cfg) != InvaginationCreatorCfg:
            raise ValueError(f"No mode 'invagination', a configuração de criação deve ser 'InvaginationCreatorCfg', mas é {type(creator_cfg)}.")

        pos = creator_cfg.CreatorType(**creator_cfg.get_pars(), rng_seed=rng_seed).create().pos
        if pos.shape[0] > 0:
            creator_cfg.num_p = pos.shape[1]

        dynamic_cfg.adjust_area_pars(creator_cfg.num_p)
        super().__init__(creator_cfg, dynamic_cfg, space_cfg, run_cfg, other_cfgs, rng_seed)

    def get_creator(self) -> Creator:
        if self.run_cfg.id is RunType.REPLAY_DATA:
            return CreatorRD()

        # return Creator(**self.creator_cfg.get_pars(), rng_seed=self.rng_seed)
        return self.creator_cfg.CreatorType(**self.creator_cfg.get_pars(), rng_seed=self.rng_seed)
    
    def get_solver(self) -> SolverCore:
        self.creator: Creator

        if self.run_cfg.id is RunType.REPLAY_DATA:
            # return SolverRD(self.run_cfg)
            return SolverReplay(self.run_cfg, self.dynamic_cfg, self.space_cfg)

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            if self.run_cfg.replay is not None:
                # return SolverReplay(self.run_cfg.replay)
                return SolverReplay(self.run_cfg.replay, self.dynamic_cfg, self.space_cfg)

        if self.run_cfg.checkpoint:
            from phystem.systems.ring.collectors import StateCheckpoint
            init_data, metadata = StateCheckpoint.load(self.run_cfg.checkpoint.folder_path)
        else:
            init_data = self.creator.create()
        
        stokes_cfg = None
        if self.other_cfgs is not None:
            stokes_cfg = self.other_cfgs.get("stokes", None)

        solver = CppSolver(**init_data.get_data(), num_particles=self.creator_cfg.num_p, 
            dynamic_cfg=self.dynamic_cfg, stokes_cfg=stokes_cfg, space_cfg=self.space_cfg,
            int_cfg=self.run_cfg.int_cfg, rng_seed=self.rng_seed)
        
        int_cfg: IntegrationCfg = self.run_cfg.int_cfg
        if int_cfg.update_type is UpdateType.INVAGINATION:
            inv_cfg: InvaginationCfg = self.other_cfgs["invagination"]
            inv_creator_cfg: InvaginationCreatorCfg = self.creator_cfg 

            solver.cpp_solver.init_invagination(
                inv_creator_cfg.height, inv_creator_cfg.length, 
                inv_cfg.upper_k, inv_cfg.bottom_k, inv_cfg.num_affected
            )

        return solver

    def run_real_time(self):
        real_time_cfg: RealTimeCfg = self.run_cfg
        graph_cfg = real_time_cfg.graph_cfg

        if graph_cfg is None:
            graph_cfg = graphs_cfg.SimpleGraphCfg()

        # fig, ax = plt.subplots()
        # fig = Figure(dpi=real_time_cfg.ui_settings.dpi)
        fig = Figure()
        ax = fig.add_subplot()

        # particles_graph = graph_cfg.GraphCls(
        #     ax=ax, solver=self.solver, space_cfg=self.space_cfg, dynamic_cfg=self.dynamic_cfg, 
        #     graph_cfg=real_time_cfg.graph_cfg)
        particles_graph = graph_type.get_graph(graph_cfg)(
            fig=fig, ax=ax, solver=self.solver, sim_configs=self.configs_container,
            graph_cfg=graph_cfg
        )

        ## Initialize graphs ###
        # particles_graph.init()

        if graph_cfg.cpp_is_debug:
            self.solver.update_visual_aids()
            particles_graph.update()

        def update(frame=None):
            control_mng: ui_components.ControlMng
            control_mng = self.app.control.control_mng

            if control_mng.is_paused and control_mng.advance_once:
               control_mng.is_paused = False 
            elif not control_mng.is_paused and control_mng.advance_once:
               control_mng.advance_once = False 
               control_mng.is_paused = True 

            if not control_mng.is_paused or control_mng.advance_once:
                i = 0
                while i < real_time_cfg.num_steps_frame:
                    if graph_cfg.pause_on_high_vel:
                        if self.solver.update_debug.high_vel:
                            control_mng.is_paused = True
                            break

                    self.time_it.decorator("solver", self.solver.update)
                    i += 1
                
            self.time_it.decorator("graph", particles_graph.update)

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            def update_video(frame=None):
                i = 0
                while i < real_time_cfg.num_steps_frame:
                    self.time_it.decorator("solver", self.solver.update)
                    i += 1

                ax.set_title(f"t = {self.solver.time}")
                self.time_it.decorator("graph", particles_graph.update)

            self.save_video(fig, update_video)
        else:
            if type(real_time_cfg) is RealTimeCfg:
                if real_time_cfg.ui_settings.ControlT is None: 
                    real_time_cfg.ui_settings.ControlT = ui_components.Control
                if real_time_cfg.ui_settings.InfoT is None: 
                    real_time_cfg.ui_settings.InfoT = ui_components.Info
            elif type(real_time_cfg) is ReplayDataCfg:
                if real_time_cfg.ui_settings.ControlT is None: 
                    real_time_cfg.ui_settings.ControlT = ui_components.ControlReplay
                if real_time_cfg.ui_settings.InfoT is None: 
                    real_time_cfg.ui_settings.InfoT = ui_components.InfoReplay
            
            self.run_app(fig, update, "Ring", real_time_cfg.ui_settings)

    def run_real_time_only_mpl(self):
        from phystem.systems.ring.ui.mpl import graph as mpl_graph
        from phystem.systems.ring.ui.mpl.widget import WidgetManager

        real_time_cfg: RealTimeCfg = self.run_cfg
        graph_cfg: graphs_cfg.BaseGraphCfg = real_time_cfg.graph_cfg

        fig, axes = self.configure_ui(real_time_cfg.id)

        widget_manager = WidgetManager(axes[WidgetType.button], axes[WidgetType.slider], real_time_cfg)

        ax_main = axes["main"]
        info_ax = axes["info"]

        ## Creates graphs ###
        particles_graph = mpl_graph.MainGraph(
            ax=ax_main, solver=self.solver, space_cfg=self.space_cfg, dynamic_cfg=self.dynamic_cfg, 
            graph_cfg=real_time_cfg.graph_cfg)
        info_graph = mpl_graph.Info(info_ax, self.solver, self.time_it, 
            self.dynamic_cfg, self.creator_cfg, self.space_cfg)

        ## Initialize graphs ###
        info_graph.init()
        particles_graph.init()
        
        if graph_cfg.begin_paused:
            widget_manager.is_paused = True

        def update(frame):
            if not widget_manager.is_paused:
                i = 0
                while i < real_time_cfg.num_steps_frame:
                    if graph_cfg.pause_on_high_vel:
                        if self.solver.update_debug.high_vel:
                            widget_manager.is_paused = True
                            break

                    self.time_it.decorator(self.solver.update)
                    i += 1

            info_graph.update()
            particles_graph.update()

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            self.save_video(fig, update)
        else:
            self.run_mpl_animation(fig, update)

    @staticmethod
    def configure_ui(run_type: RunType):
        '''
        Configura as posições e tamanhos dos elementos gráficos.
        '''
        from phystem.gui_phystem.mpl.gui_config import StandardGui
        from phystem.gui_phystem.mpl.geometry import VerticalGeometry
        from phystem.gui_phystem.mpl.widget import WidgetType

        fig, axes, space_mngs = StandardGui().run(panel_width=0.35, widget_width=0.8)
        widget_space_mng: VerticalGeometry = space_mngs["widgets"]

        #==
        # Widgets
        #==
        circles_button_ax = fig.add_axes(widget_space_mng.get_new_rect("circles", WidgetType.button))
        cb_forces_ax = fig.add_axes(widget_space_mng.get_new_rect("check_buttons", WidgetType.button))
        cb_pos_cont = fig.add_axes(widget_space_mng.get_new_rect("cb_pos_cont", WidgetType.button))

        freq_slider_ax = None
        if run_type is RunType.REPLAY_DATA:
            freq_slider_ax = fig.add_axes(widget_space_mng.get_new_rect("freq", WidgetType.slider))

        axes[WidgetType.button]["circles"] = circles_button_ax
        axes[WidgetType.button]["check_buttons"] = cb_forces_ax
        axes[WidgetType.button]["cb_pos_cont"] = cb_pos_cont
        axes[WidgetType.slider]["freq"] = freq_slider_ax

        #==
        # Widget reorder
        #==
        widgets_order = (
            ("pause", WidgetType.button), 
            ("circles", WidgetType.button),
            ("check_buttons", WidgetType.button),
            ("cb_pos_cont", WidgetType.button),
            ("speed", WidgetType.slider),
            ("freq", WidgetType.slider),
        )
    
        axes_correct_order = {WidgetType.button: {}, WidgetType.slider: {}}
        for id, (default_name, wg_type) in enumerate(widget_space_mng.widget_order):
            axes_correct_order[widgets_order[id][1]][widgets_order[id][0]] = axes[wg_type][default_name]

        for wg_type, wg_axes in axes_correct_order.items():
            axes[wg_type] = wg_axes

        return fig, axes