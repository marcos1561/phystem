import matplotlib.pyplot as plt

from phystem.core.simulation import SimulationCore

from phystem.gui_phystem.mpl import graph

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
        fig = plt.Figure()
        ax = fig.add_subplot()
        
        particle_graph = graph.ParticlesGraph(
            ax=ax, 
            pos=self.solver.pos, 
            space_size=self.space_cfg.size,
        )

        def update(frame):
            if not self.app.control.control_mng.is_paused:
                self.solver.update()
            
            particle_graph.update()


        from phystem.core.run_config import RunType
        
        if self.run_cfg.id is RunType.REAL_TIME:
            self.run_app(fig, update)
        elif self.run_cfg.id is RunType.SAVE_VIDEO:
            self.save_video(fig, update)

