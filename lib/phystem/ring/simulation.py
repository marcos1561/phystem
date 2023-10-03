import matplotlib.pyplot as plt
import matplotlib.animation as animation

from phystem.core.run_config import RealTimeCfg, SaveCfg, RunType

from phystem.core.simulation import SimulationCore
from phystem.core.solvers import SolverCore
from phystem.ring.configs import CreateCfg
from phystem.ring.creators import Creator, InitData, CreatorRD
from phystem.ring.solvers import CppSolver, SolverRD

from phystem.ring.ui.graph import Info, MainGraph
from phystem.ring.ui.widget import WidgetManager
from ui_phystem.widget import WidgetType

class Simulation(SimulationCore):
    def get_creator(self) -> Creator:
        self.create_cfg: CreateCfg

        if self.run_cfg.id is RunType.REPLAY_DATA:
            return CreatorRD()

        return Creator(**self.create_cfg.get_pars())
    
    def get_solver(self) -> SolverCore:
        if self.run_cfg.id is RunType.REPLAY_DATA:
            return SolverRD(self.run_cfg)
        
        init_data: InitData = self.creator.create()
        
        solver = CppSolver(**init_data.get_data(), dynamic_cfg=self.dynamic_cfg, size=self.space_cfg.size,
            dt=self.run_cfg.dt, rng_seed=self.rng_seed)
        
        return solver

    def run_real_time(self):
        real_time_cfg: RealTimeCfg = self.run_cfg
        self.solver: CppSolver

        fig, axes = self.configure_ui(real_time_cfg.id)

        widget_manager = WidgetManager(axes[WidgetType.button], axes[WidgetType.slider], real_time_cfg)

        ax_main = axes["main"]
        info_ax = axes["info"]

        ## Creates graphs managers ###
        particles_graph = MainGraph(
            ax=ax_main, solver=self.solver, space_cfg=self.space_cfg, dynamic_cfg=self.dynamic_cfg, 
            graph_cfg=real_time_cfg.graph_cfg)
        info_graph = Info(info_ax, self.solver, self.time_it, 
            self.dynamic_cfg, self.create_cfg, self.space_cfg)

        ## Initialize graphs ###
        info_graph.init()
        particles_graph.init()

        def update(frame):
            if not widget_manager.is_paused:
                i = 0
                while i < real_time_cfg.num_steps_frame:
                    self.time_it.decorator(self.solver.update)
                    i += 1

            info_graph.update()
            particles_graph.update()

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            from ic_utils.progress import MplAnim as Progress
            save_video_cfg: SaveCfg = self.run_cfg

            frames = save_video_cfg.num_frames
            progress = Progress(frames, 10)
            ani = animation.FuncAnimation(fig, update, frames=frames)
        
            ani.save(save_video_cfg.path, fps=save_video_cfg.fps, progress_callback=progress.update)
        else:
            ani = animation.FuncAnimation(fig, update, interval=1/(real_time_cfg.fps)*1000, cache_frame_data=False)
            plt.show()

    @staticmethod
    def configure_ui(run_type: RunType):
        '''
        Configura as posições e tamanhos dos elementos gráficos.
        '''
        from ui_phystem.space_config import StandardSpace
        from ui_phystem.geometry import SpaceManager
        from ui_phystem.widget import WidgetType

        fig, axes, space_mngs = StandardSpace().run(panel_width=0.25, widget_width=0.8)
        widget_space_mng: SpaceManager = space_mngs["widgets"]

        #==
        # Widgets
        #==
        circles_button_ax = fig.add_axes(widget_space_mng.get_new_rect("circles", WidgetType.button))
        check_buttons_ax = fig.add_axes(widget_space_mng.get_new_rect("check_buttons", WidgetType.button))

        freq_slider_ax = None
        if run_type is RunType.REPLAY_DATA:
            freq_slider_ax = fig.add_axes(widget_space_mng.get_new_rect("freq", WidgetType.slider))

        axes[WidgetType.button]["circles"] = circles_button_ax
        axes[WidgetType.button]["check_buttons"] = check_buttons_ax
        axes[WidgetType.slider]["freq"] = freq_slider_ax

        #==
        # Widget reorder
        #==
        widgets_order = (
            ("pause", WidgetType.button), 
            ("circles", WidgetType.button),
            ("check_buttons", WidgetType.button),
            ("speed", WidgetType.slider),
            ("freq", WidgetType.slider),
        )
    
        axes_correct_order = {WidgetType.button: {}, WidgetType.slider: {}}
        for id, (default_name, wg_type) in enumerate(widget_space_mng.widget_order):
            axes_correct_order[widgets_order[id][1]][widgets_order[id][0]] = axes[wg_type][default_name]

        for wg_type, wg_axes in axes_correct_order.items():
            axes[wg_type] = wg_axes


        return fig, axes