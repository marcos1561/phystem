import matplotlib.pyplot as plt
import matplotlib.animation as animation


from phystem.core.simulation import SimulationCore
from phystem.core.run_config import RealTimeCfg, SaveCfg, RunType

from phystem.gui_phystem.gui_config import StandardGui
from phystem.gui_phystem import widget, graph

from phystem.systems.random_walker.creator import Creator 
from phystem.systems.random_walker.solver import Solver 
from phystem.systems.random_walker.configs import SpaceCfg, CreatorCfg, DynamicCfg


class Simulation(SimulationCore): 
    dynamic_cfg: DynamicCfg
    creator_cfg: CreatorCfg
    space_cfg: SpaceCfg
    solver: Solver

    def get_creator(self):
        return Creator(
            speed=self.creator_cfg.speed,
            size=self.creator_cfg.size,
        )
            
    def get_solver(self):
        po0, vel0 = self.creator.create()

        return Solver(
            po0, vel0,
            noise_strength = self.dynamic_cfg.noise_strength,
            size = self.space_cfg.size,
            dt = self.run_cfg.int_cfg.dt,
        )

    def run_real_time(self):
        real_time_cfg: RealTimeCfg = self.run_cfg

        # fig, axes, space_mngs = StandardGui().run()
        fig, ax_walker = plt.subplots()

        # widget_manager = widget.StandardManager(
        #     axes[widget.WidgetType.button], 
        #     axes[widget.WidgetType.slider], 
        #     real_time_cfg,
        # )

        # info_ax = axes["info"]

        particles_graph = graph.ParticlesGraph(
            ax=ax_walker, 
            pos=self.solver.pos, 
            space_size=self.space_cfg.size,
        )
        
        # info_graph = graph.Info(info_ax, self.solver, self.time_it, 
        #     self.dynamic_cfg, self.creator_cfg, self.space_cfg)

        ## Initialize graphs ###
        particles_graph.init()
        # info_graph.init()

        def update(frame):
            # if not widget_manager.is_paused:
            # i = 0
            # while i < real_time_cfg.num_steps_frame:
                # self.time_it.decorator(self.solver.update)
                # i += 1

            # info_graph.update()
            self.solver.update()
            particles_graph.update()

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            from phystem.utils.progress import MplAnim as Progress
            import os, yaml
            save_video_cfg: SaveCfg = self.run_cfg
            
            folder_path = save_video_cfg.path.split("/")[0]
            video_name = save_video_cfg.path.split("/")[-1].split(".")[0]
            if not os.path.exists(folder_path):
                raise Exception(f"O caminho {folder_path} não existe.")

            frames = save_video_cfg.num_frames
            progress = Progress(frames, 10)
            ani = animation.FuncAnimation(fig, update, frames=frames)

            config_path = os.path.join(folder_path, f"{video_name}_config.yaml")
            with open(config_path, "w") as f:
                yaml.dump(self.configs, f)
            ani.save(save_video_cfg.path, fps=save_video_cfg.fps, progress_callback=progress.update)
        else:
            ani = animation.FuncAnimation(fig, update, interval=1/(real_time_cfg.fps)*1000, cache_frame_data=False)
            plt.show()

