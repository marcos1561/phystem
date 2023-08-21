from physical_system.simulation import Simulation
from physical_system.configs import *

self_propelling_cfg = SelfPropellingCfg(
    mobility = 1.,
    relaxation_time = 1.,
    nabla = 0,
    vo = 1.,
    max_repulsive_force = 30.,
    max_attractive_force = 0.75,
    r_eq =  5/6,
    max_r = 1.,
)

space_cfg = SpaceCfg(
    size = 40.824829,
)

create_cfg = CreateCfg(
    n = 1000,
    r = space_cfg.size/2,
    type = CreateType.SQUARE,
)

# seed = 40028922
seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    dt = 0.05,
    num_steps_frame = 20,
    fps = 60,
    solver_type = SolverType.CPP,
    update_type = UpdateType.NORMAL,
)

collect_data_cfg = CollectDataCfg(
    tf = 1000,
    dt = 0.05,
    folder_path="data_test/only_final/truth",
    solver_type=SolverType.CPP,
    update_type=UpdateType.NORMAL,
    only_last=False,
)

save_cfg = SaveCfg(
    path = "data/teste_teste.mp4",
    speed=5,
    fps=30, 
    dt=0.05,
    duration=5,
    tf=None,
    solver_type=SolverType.CPP,
    update_type=UpdateType.WINDOWS,
)

run_type_to_cfg = {RunType.COLLECT_DATA: collect_data_cfg, RunType.REAL_TIME: real_time_cfg, RunType.SAVE_VIDEO: save_cfg}
sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
