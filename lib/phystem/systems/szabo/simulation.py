import matplotlib.pyplot as plt
import matplotlib.animation as animation

from phystem.systems.szabo import creators 
import phystem.systems.szabo.solvers as solvers 
from phystem.systems.szabo.ui.graph import ParticlesGraph, Info, MeanVelGraph

from phystem.core.run_config import RunType, SolverType
from phystem.systems.szabo.run_config import RealTimeCfg, SaveCfg
from phystem.systems.szabo.configs import CreatorCfg
from phystem.core.simulation import SimulationCore 
import phystem.core.creators as core_creator 
from phystem.systems.szabo.ui.widget import WidgetManager
from phystem.gui_phystem.widget import WidgetType

class Simulation(SimulationCore): 
    creator_cfg: CreatorCfg
    def get_creator(self):

        if self.run_cfg.id is RunType.REPLAY_DATA:
            return creators.CreatorRD()
        
        return creators.Particles(**self.creator_cfg.get_pars(), rng_seed=self.rng_seed)
            
    def get_solver(self):
        self.creator.create()

        if self.run_cfg.id is RunType.REPLAY_DATA:
            return solvers.SolverRD(self.run_cfg)
        
        solver_type = self.run_cfg.solver_type

        if solver_type is SolverType.CPP:
            return solvers.CppSolver(self.creator.pos, self.creator.vel, self.dynamic_cfg,
                self.space_cfg.size, self.run_cfg.dt, self.run_cfg.num_windows, self.run_cfg.update_type, self.rng_seed)  
        elif solver_type is SolverType.PYTHON:
            raise Exception("Python solver ainda não implementado.")

    def run_real_time(self):
        real_time_cfg: RealTimeCfg = self.run_cfg

        fig, axes = self.configure_ui(real_time_cfg.id)

        widget_manager = WidgetManager(axes[WidgetType.button], axes[WidgetType.slider], real_time_cfg)

        ax_particles = axes["main"]
        # mean_vel_ax = axes["mean_vel"]
        info_ax = axes["info"]

        ## Creates graphs managers ###
        particles_graph = ParticlesGraph(
            ax=ax_particles, solver=self.solver, space_cfg=self.space_cfg, dynamic_cfg=self.dynamic_cfg, 
            graph_cfg=real_time_cfg.graph_cfg)
        # mean_vel_graph = MeanVelGraph(mean_vel_ax, self.solver)
        info_graph = Info(info_ax, self.solver, self.time_it, 
            self.dynamic_cfg, self.creator_cfg, self.space_cfg)

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
            # mean_vel_graph.update()

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            from phystem.utils.progress import MplAnim as Progress
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
        from phystem.gui_phystem.gui_config import StandardGui
        from phystem.gui_phystem.widget import WidgetType
        from phystem.gui_phystem.geometry import VerticalGeometry

        fig, axes, space_mngs = StandardGui().run()
        widget_space_mng: VerticalGeometry = space_mngs["widgets"]

        #==
        # Widgets
        #==
        circles_button_ax = fig.add_axes(widget_space_mng.get_new_rect("circles", WidgetType.button))

        freq_slider_ax = None
        if run_type is RunType.REPLAY_DATA:
            freq_slider_ax = fig.add_axes(widget_space_mng.get_new_rect("freq", WidgetType.slider))

        axes[WidgetType.button]["circles"] = circles_button_ax
        axes[WidgetType.slider]["freq"] = freq_slider_ax

        #==
        # Mean vel
        #==
        h_pad = 0.05
        bottom = 0.05

        particle_rect = axes["main"].get_position().bounds
        left = particle_rect[0] + particle_rect[2] + h_pad
        # mean_vel_ax = fig.add_axes([
        #     left,
        #     bottom, 
        #     1 - left - 0.01,
        #     0.9
        # ])

        # axes["mean_vel"] = mean_vel_ax

        #==
        # Widget reorder
        #==
        widgets_order = (
            ("pause", WidgetType.button), 
            ("circles", WidgetType.button),
            ("speed", WidgetType.slider),
            ("freq", WidgetType.slider),
        )
    
        axes_correct_order = {WidgetType.button: {}, WidgetType.slider: {}}
        for id, (default_name, wg_type) in enumerate(widget_space_mng.widget_order):
            axes_correct_order[widgets_order[id][1]][widgets_order[id][0]] = axes[wg_type][default_name]

        for wg_type, wg_axes in axes_correct_order.items():
            axes[wg_type] = wg_axes


        return fig, axes
