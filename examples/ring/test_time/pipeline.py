from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import CollectDataCfg

def collect_times(sim: Simulation, collect_cfg): 
    solver = sim.solver
    cfg: CollectDataCfg = sim.run_cfg

    timer = sim.time_it
    
    time_data = []
    # prog = progress.Continuos(tf)

    num_points: int = collect_cfg["num_points"]
    freq = int(((cfg.tf)/cfg.int_cfg.dt)/num_points)
    if freq == 0:
        freq = 1

    count = 0
    while solver.time < cfg.tf:
        timer.decorator(solver.update)
        # prog.update(solver.time)
        count += 1

        if count % freq == 0:
            time_data.append(timer.mean_time())

    import pickle, os
    with open(os.path.join(cfg.folder_path, collect_cfg["file_name"] + ".pickle"), "wb") as f:
        pickle.dump(time_data, f)