import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.animation as animation

from physical_system.solver import VicsekSolver, CppSolver
from physical_system.particles import Particles
from physical_system.graph import ParticlesGraph, Info, MeanVelGraph
from physical_system.configs import *
from ic_utils.timer import TimeIt

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
        self.particles = Particles(self.create_cfg, self.rng_seed)
        self.particles.create()

        if self.run_cfg.solver_type is SolverType.PYTHON:
            raise Exception("Python solver ainda não implementado.")
        elif self.run_cfg.solver_type == SolverType.CPP:
            self.solver = CppSolver(self.particles.pos, self.particles.vel, self.self_propelling_cfg,
                self.space_cfg.size, self.run_cfg.dt, self.run_cfg.update_type, self.rng_seed)
            self.particles.pos = self.solver.cpp_solver.py_pos

    def run(self):
        if self.run_cfg.id in RunType.REAL_TIME | RunType.SAVE_VIDEO:
            self.run_real_time()
        elif self.run_cfg.id is RunType.COLLECT_DATA:
            self.run_only_sim()

    def run_only_sim(self):
        import physical_system.collectors as collectors
        from metcompb import progress
        run_cfg: CollectDataCfg = self.run_cfg

        num_points = 1000
        nabla_range = np.linspace(0, 1, 4)
        nabla_range = np.array([0])
        
        prog = progress.Continuos(nabla_range.max())
        
        time_data = None
        mean_vel_data = np.zeros((nabla_range.size, num_points))
        for id, nabla in enumerate(nabla_range):
            self.self_propelling_cfg.nabla = nabla
            self.init_sim()

            collector = collectors.MeanVel(
                self.solver, run_cfg.tf, run_cfg.dt,
                num_points=num_points, path=run_cfg.folder_path,
            )

            count = 0
            while self.solver.time < run_cfg.tf:
                self.solver.update()
                collector.collect(count)
                
                count += 1
            
            prog.update(nabla)

            mean_vel_data[id] = collector.data[0]     
            time_data = collector.data[1]     
        
        import os
        folder_path = "data/self_propelling/nabla"
        np.save(os.path.join(folder_path, "mean_vel.npy"), mean_vel_data)
        np.save(os.path.join(folder_path, "nabla.npy"), nabla_range)
        np.save(os.path.join(folder_path, "time.npy"), time_data)

        return 

        prog = progress.Continuos(self.run_cfg.tf)
        if not run_cfg.only_last:
            state_collector = collectors.State(
                self.solver, run_cfg.folder_path, 
                tf=run_cfg.tf, dt=run_cfg.dt
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
        self.run_cfg: RealTimeCfg

        ## Creates and set figure and axes ###
        # fig, ax_particles = plt.subplots()
        fig, (ax_particles, mean_vel_ax) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [1, 1]})
        
        # from matplotlib.axes import Axes
        # mean_vel_ax: Axes
        # rect = mean_vel_ax.get_position().bounds
        # mean_vel_ax.set_position((rect[0], rect[1], rect[2]*.8, rect[3]*.8))
        
        info_ax = fig.add_axes([0.02, 0.95, 0.3, 0.04])
        
        fig.set_size_inches(fig.get_size_inches()[0]*2, fig.get_size_inches()[1]*1.3)
        # fig.set_size_inches(w=fig.get_size_inches()[0]*1.5, h=fig.get_size_inches()[1])
        fig.subplots_adjust(right=0.980, top=1)
        
        ## Creates graphs managers ###
        particles_graph = ParticlesGraph(ax_particles, self.particles, self.space_cfg)
        mean_vel_graph = MeanVelGraph(mean_vel_ax, self.solver)


        info_graph = Info(info_ax, self.solver, self.time_it, 
            self.self_propelling_cfg, self.create_cfg, self.space_cfg)

        ## Initialize graphs ###
        info_graph.init()
        particles_graph.init()

        def update(frame):
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
