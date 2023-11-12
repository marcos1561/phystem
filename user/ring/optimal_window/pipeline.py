import numpy as np
import yaml, os

from phystem.systems.ring.configs import *

from phystem.systems.ring.simulation import Simulation
from phystem.utils import progress

class Pipeline:
    def __init__(self, configs) -> None:
        self.configs = configs
        self.sim: Simulation = None

    def reset(self):
        self.sim = Simulation(**self.configs)

    def set_init_cfg(self, n: int):
        k = 1.4
        radius = 20/6 * 1.5
        num_rings = n**2
        l = 2 * k * radius

        space_cfg = SpaceCfg(
            size = n * l,
        )

        centers = []
        for j in range(n):
            y = k * radius + j * l - space_cfg.size/2
            for i in range(n):
                x = k * radius + i * l - space_cfg.size/2
                centers.append([x, y])

        creator_cfg = CreatorCfg(
            num_rings = num_rings,
            num_p = 30,
            r = radius,
            angle=np.random.random(num_rings)*2*np.pi,
            center= centers,
        )

        self.configs["space_cfg"] = space_cfg
        self.configs["creator_cfg"] = creator_cfg

    def run(self):
        n_to_folder_path = {
            3: "data/run2",
            8: "data/run3", 
        } 

        for n in [3, 8]:
            folder_path = n_to_folder_path[n]
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)

            self.set_init_cfg(n)

            config_path = os.path.join(folder_path, "config.yaml")
            with open(config_path, "w") as f:
                yaml.dump(self.configs, f)

            tf = 15
            num_points = 1000
            dt = self.configs["run_cfg"].dt

            freq = int(((tf)/dt)/num_points)
            if freq == 0:
                freq = 1

            time_data = []

            from math import ceil
            max_num_windows = int(ceil(self.configs["space_cfg"].size/(self.configs["dynamic_cfg"].diameter*1.2))) 
            
            if n == 8:
                num_windows_range = range(3, max_num_windows+1, 3)
            else:
                num_windows_range = range(3, max_num_windows+1)
            
            prog = progress.Discrete(len(num_windows_range), 10)

            for id, num_windows in enumerate(num_windows_range):
                prog.update(id)

                self.configs["run_cfg"].num_col_windows = num_windows
                self.reset()
                solver = self.sim.solver
                timer = self.sim.time_it
                
                time_data_i = []
                # prog = progress.Continuos(tf)

                count = 0
                while solver.time < tf:
                    timer.decorator(solver.update)
                    # prog.update(solver.time)
                    count += 1

                    if count % freq == 0:
                        time_data_i.append(timer.mean_time())

                time_data.append(time_data_i)
            
            prog.update(len(num_windows_range))
            np.save(os.path.join(folder_path, "data.npy"), np.array(time_data))
            np.save(os.path.join(folder_path, "num_windows.npy"), np.array(num_windows_range))