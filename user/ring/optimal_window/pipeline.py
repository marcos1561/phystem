import numpy as np

from phystem.systems.ring.simulation import Simulation
from phystem.utils import progress

class Pipeline:
    def __init__(self, configs) -> None:
        self.configs = configs
        self.sim: Simulation = None

    def reset(self):
        self.sim = Simulation(**self.configs)

    def run(self):
        tf = 15
        num_points = 1000
        dt = self.configs["run_cfg"].dt

        freq = int(((tf)/dt)/num_points)
        if freq == 0:
                freq = 1

        
        time_data = []
        num_windows_arr = [20, 21, 22, 23, 24]
        for num_windows in num_windows_arr:
            self.configs["run_cfg"].num_col_windows = num_windows
            self.reset()
            solver = self.sim.solver
            timer = self.sim.time_it
            
            time_data_i = []
            prog = progress.Continuos(tf)

            count = 0
            while solver.time < 15:
                timer.decorator(solver.update)
                prog.update(solver.time)
                count += 1

                if count % freq == 0:
                    time_data_i.append(timer.mean_time())

            time_data.append(time_data_i)
        
        np.save("data.npy", np.array(time_data))
        np.save("num_windows.npy", np.array(num_windows_arr))


    
     