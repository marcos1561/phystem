import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
import matplotlib.animation as animation

from physical_system.solver import VicsekSolver, CppSolver
from physical_system.particles import Particles
from physical_system.graph import ParticlesGraph, Info, MeanVelGraph
from physical_system.configs import *
from ic_utils.timer import TimeIt

class WidgetManager:
    def __init__(self, buttons_ax, slider_ax, run_cfg: RealTimeCfg) -> None:
        self.run_cfg = run_cfg

        self.buttons = {}
        self.sliders: dict[str, Slider] = {}
        
        self.buttons["pause"] = Button(buttons_ax["pause"], "Pause")
        self.buttons["circles"] = Button(buttons_ax["circles"], "Show Circles")

        self.buttons["pause"].on_clicked(self.pause_callback)
        self.buttons["circles"].on_clicked(self.circles_callback)
        
        self.sliders["speed"] = Slider(
            ax=slider_ax["speed"],
            label="speed",
            valmin=1,
            valmax=100,
            valstep=1,
            valinit=run_cfg.num_steps_frame
        )
        self.sliders["speed"].label.set_position((0, 1)) 
        self.sliders["speed"].label.set_horizontalalignment("left")
        self.sliders["speed"].on_changed(self.speed_callback)
        
        if run_cfg.id is RunType.SAVED_DATA:
            self.sliders["freq"] = Slider(
                ax=slider_ax["freq"],
                label="freq",
                valmin=0,
                valmax=10,
                valstep=1,
                valinit=run_cfg.frequency
            )
            self.sliders["freq"].label.set_position((0, 1)) 
            self.sliders["freq"].label.set_horizontalalignment("left")
            self.sliders["freq"].on_changed(self.freq_callback)

        self.is_paused = False

    def pause_callback(self, event):
        if self.is_paused:
            self.is_paused = False
        else:
            self.is_paused = True
   
    def circles_callback(self, event):
        if self.run_cfg.graph_cfg.show_circles:
            self.run_cfg.graph_cfg.show_circles = False
        else:
            self.run_cfg.graph_cfg.show_circles = True
    
    def speed_callback(self, val):
        self.run_cfg.num_steps_frame = int(val)
    
    def freq_callback(self, val):
        self.run_cfg.frequency = int(val)

class Simulation: 
    '''
    Simulates the rope with the given configurations and plot the simulation.
    '''
    def __init__(self, create_cfg: CreateCfg, self_propelling_cfg: SelfPropellingCfg,
        space_cfg: SpaceCfg, run_cfg: RunCfg, rng_seed: float=None) -> None:
        self.create_cfg = create_cfg
        self.space_cfg = space_cfg
        self.self_propelling_cfg = self_propelling_cfg
        self.run_cfg = run_cfg

        self.time_it = TimeIt(num_samples=200)

        self.rng_seed = rng_seed

        self.init_sim()        

    def init_sim(self):
        if self.run_cfg.id is RunType.SAVED_DATA:
            class SolverSD:
                def __init__(self, run_cfg: SavedDataCfg) -> None:
                    self.pos = np.load("data/self_propelling/teste/pos.npy")
                    self.vel = np.load("data/self_propelling/teste/vel.npy")
                    self.time_arr = np.load("data/self_propelling/teste/time.npy")
                    
                    self.num_particles = self.pos.shape[2]
                    self.id = 0
                    self.dt = 0
                    
                    self.run_cfg = run_cfg
                    self.count = 0

                @property
                def time(self):
                    return self.time_arr[self.id]    

                def mean_vel(self):
                    id = self.id
                    speeds = np.sqrt(self.vel[id][0]**2 + self.vel[id][1]**2)
                    speeds[speeds < 1e-6] = 1e-6
                    m_vel = (self.vel[id] / speeds).sum(axis=1) / self.num_particles
                    return (m_vel[0]**2 + m_vel[1]**2)**.5

                def mean_vel_vec(self):
                    return [0, 1]

                def update(self):
                    self.count += 1
                    if self.count > self.run_cfg.frequency:
                        self.count = 0
                        self.id += 1


            class ParticlesSD:
                def __init__(self, solver: SolverSD) -> None:
                    self.solver = solver

                def plot(self):
                    return self.solver.pos[self.solver.id]

            self.solver = SolverSD(self.run_cfg)
            self.particles = ParticlesSD(self.solver)
            return
        
        self.particles = Particles(self.create_cfg, self.rng_seed)
        self.particles.create()

        if self.run_cfg.solver_type is SolverType.PYTHON:
            raise Exception("Python solver ainda não implementado.")
        elif self.run_cfg.solver_type == SolverType.CPP:
            self.solver = CppSolver(self.particles.pos, self.particles.vel, self.self_propelling_cfg,
                self.space_cfg.size, self.run_cfg.dt, self.run_cfg.update_type, self.rng_seed)
            self.particles.pos = self.solver.cpp_solver.py_pos

    def run(self):
        if self.run_cfg.id in RunType.REAL_TIME | RunType.SAVE_VIDEO | RunType.SAVED_DATA:
            self.run_real_time()
        elif self.run_cfg.id is RunType.COLLECT_DATA:
            self.run_only_sim()

    def run_only_sim(self):
        import physical_system.collectors as collectors
        from metcompb import progress
        run_cfg: CollectDataCfg = self.run_cfg

        # num_points = 1000
        # nabla_range = np.linspace(0, 1, 20)
        # nabla_range = np.array([0])
        
        # prog = progress.Continuos(nabla_range.max())
        
        # time_data = None
        # mean_vel_data = np.zeros((nabla_range.size, num_points))
        # for id, nabla in enumerate(nabla_range):
        #     self.self_propelling_cfg.nabla = nabla
        #     self.init_sim()

        #     collector = collectors.MeanVel(
        #         self.solver, run_cfg.tf, run_cfg.dt,
        #         num_points=num_points, path=run_cfg.folder_path,
        #     )

        #     count = 0
        #     while self.solver.time < run_cfg.tf:
        #         self.solver.update()
        #         collector.collect(count)
        #         count += 1
            
        #     prog.update(nabla)

        #     mean_vel_data[id] = collector.data[0]     
        #     time_data = collector.data[1]     
        
        # import os
        # folder_path = "data/self_propelling/nabla"
        # np.save(os.path.join(folder_path, "mean_vel.npy"), mean_vel_data)
        # np.save(os.path.join(folder_path, "nabla.npy"), nabla_range)
        # np.save(os.path.join(folder_path, "time.npy"), time_data)

        # return 

        prog = progress.Continuos(self.run_cfg.tf)
        if not run_cfg.only_last:
            # state_collector = collectors.State(
            #     self.solver, run_cfg.folder_path, 
            #     to=100, tf=300, dt=run_cfg.dt
            # )
            state_collector = collectors.State(
                self.solver, run_cfg.folder_path, 
                dt=run_cfg.dt, tf=run_cfg.tf, num_points=1000,
            )
            
            state_collector.collect(0)
            count = 0
            while self.solver.time < run_cfg.tf:
                self.solver.update()
                state_collector.collect(count)
                
                prog.update(self.solver.time)
                count += 1
            
            state_collector.save()
        else:
            state_collector = collectors.State(
                self.solver, run_cfg.folder_path, 
                num_points=2,
            )
            
            state_collector.collect(0)
            while self.solver.time < run_cfg.tf:
                self.solver.update()
                prog.update(self.solver.time)
            
            state_collector.collect(1)
            state_collector.save()

    def run_real_time(self):
        '''
        Run the simulation while plotting it.
        '''
        run_cfg: RealTimeCfg = self.run_cfg
        self.run_cfg = run_cfg

        fig, axes = self.configure_ui(run_cfg.id)

        widget_manager = WidgetManager(axes["buttons"], axes["sliders"], self.run_cfg)

        ## Creates graphs managers ###
        ax_particles = axes["particles"]
        mean_vel_ax = axes["mean_vel"]
        info_ax = axes["info"]

        particles_graph = ParticlesGraph(ax_particles, self.particles, self.space_cfg, self.self_propelling_cfg, 
            self.run_cfg.graph_cfg)
        mean_vel_graph = MeanVelGraph(mean_vel_ax, self.solver)
        info_graph = Info(info_ax, self.solver, self.time_it, 
            self.self_propelling_cfg, self.create_cfg, self.space_cfg)

        ## Initialize graphs ###
        info_graph.init()
        particles_graph.init()

        def update(frame):
            if not widget_manager.is_paused:
                i = 0
                while i < self.run_cfg.num_steps_frame:
                    self.time_it.decorator(self.solver.update)
                    i += 1

            info_graph.update()
            particles_graph.update()
            mean_vel_graph.update()

        if self.run_cfg.id is RunType.SAVE_VIDEO:
            self.run_cfg: SaveCfg

            from metcompb.progress import Discrete
            
            class Progress(Discrete):
                def update(self, t: int, _: int):
                    super().update(t)

            frames = self.run_cfg.num_frames
            progress = Progress(frames, 10)
            ani = animation.FuncAnimation(fig, update, frames=frames)
        
            ani.save(self.run_cfg.path, fps=self.run_cfg.fps, progress_callback=progress.update)
        else:
            ani = animation.FuncAnimation(fig, update, interval=1/(self.run_cfg.fps)*1000)
            plt.show()
    
    @staticmethod
    def configure_ui(run_type: RunType):
        from ui_geometry import managers

        fig = plt.figure()
        axes = {}

        width = 0.2
        x_pad = 0.01
        y_pad = 0.01
        rel_y_pad = 0.01

        vertical_space = 1 - 2 * y_pad - rel_y_pad
        buttons_v_space = vertical_space/2
        info_v_space = vertical_space/2

        #==
        # Widgets
        #==
        bottom = y_pad
        left = x_pad
        buttons_ax = fig.add_axes([left, bottom, width, buttons_v_space], xticks=[], yticks=[])

        buttons_manager = managers.Buttons(buttons_ax.get_position().bounds, rel_pad=0.02)
        pause_button_ax = fig.add_axes(buttons_manager.get_new_rect())
        circles_button_ax = fig.add_axes(buttons_manager.get_new_rect())
        speed_slider_ax = fig.add_axes(buttons_manager.get_new_rect())
        
        freq_slider_ax = None
        if run_type is RunType.SAVED_DATA:
            freq_slider_ax = fig.add_axes(buttons_manager.get_new_rect())

        axes["buttons"] = {
            "pause": pause_button_ax,
            "circles": circles_button_ax,
        }
        axes["sliders"] = {
            "speed": speed_slider_ax,
            "freq": freq_slider_ax,
        }

        #==
        # Info
        #==
        bottom = y_pad + buttons_v_space + rel_y_pad
        left = x_pad
        info_ax = fig.add_axes([left, bottom, width, info_v_space], xticks=[], yticks=[])
        axes["info"] = info_ax

        #==
        # Particles - Main
        #==
        h_pad = 0.01
        bottom = 0.05

        info_rect = info_ax.get_position().bounds
        
        left = info_rect[0] + info_rect[2] + 0.05 
        h_space = 1 - left
        particles_ax = fig.add_axes([
            left,
            bottom, 
            h_space/2,
            0.9
        ])

        axes["particles"] = particles_ax

        #==
        # Mean vel
        #==
        h_pad = 0.05
        bottom = 0.05

        particle_rect = particles_ax.get_position().bounds
        left = particle_rect[0] + particle_rect[2] + h_pad
        mean_vel_ax = fig.add_axes([
            left,
            bottom, 
            1 - left - 0.01,
            0.9
        ])

        axes["mean_vel"] = mean_vel_ax

        fig.set_size_inches(fig.get_size_inches()[0]*2.1, fig.get_size_inches()[1]*1.3)

        return fig, axes


