from phystem.self_propelling.simulation import Simulation
import phystem.self_propelling.collect_pipelines as collect_pipelines
from phystem.self_propelling.configs import *
from phystem.core.run_config import UpdateType, SolverType, ReplayDataCfg, RunType
from phystem.self_propelling.run_config import CollectDataCfg, RealTimeCfg, SaveCfg, GraphCfg


self_propelling_cfg = SelfPropellingCfg(
    mobility = 1.,
    relaxation_time = 1.,
    nabla = 3,
    vo = 1.,
    max_repulsive_force = 30.,
    max_attractive_force = 0.75,
    r_eq =  5/6,
    max_r = 1.,
)

space_cfg = SpaceCfg(
    # size = 18.2574185,
    # size = 57.73502691, # 0.3
    # size = 40.824829046, # 0.6
    size = 30, # 0.6
)

create_cfg = CreateCfg(
    n = 500,
    r = space_cfg.size/2,
    type = CreateType.SQUARE,
)

seed = 40028922
# seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    dt = 0.01,
    num_windows=10,
    num_steps_frame = 20,
    fps = 60,
    solver_type = SolverType.CPP,
    update_type = UpdateType.WINDOWS,
    graph_cfg = GraphCfg(
        show_circles=False),
)

replay_data_cfg = None
if run_type is RunType.REPLAY_DATA:
    replay_data_cfg = ReplayDataCfg(
        directory="data/self_propelling/teste",
        num_steps_frame=3,
        frequency=0,
        system_cfg = {
            "create_cfg": create_cfg,
            "dynamic_cfg": self_propelling_cfg,
            "space_cfg": space_cfg
        },
    )

collect_data_cfg = CollectDataCfg(
    tf = 100,
    dt = 0.01,
    num_windows=10,
    folder_path="data/self_propelling/teste",
    func = collect_pipelines.state,
    # func_id = collect_pipelines.FuncID.state,
    # get_func= collect_pipelines.get_func,
    func_cfg = collect_pipelines.CollectPlCfg(
        only_last=False, 
    ),
    solver_type=SolverType.CPP,
    update_type=UpdateType.WINDOWS,
)

save_cfg = SaveCfg(
    path = "data/teste_teste.mp4",
    speed=5,
    fps=60, 
    dt=0.01,
    duration=5,
    tf=None,
    num_windows=10,
    solver_type=SolverType.CPP,
    update_type=UpdateType.WINDOWS,
)

run_type_to_cfg = {RunType.COLLECT_DATA: collect_data_cfg, RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg, RunType.REPLAY_DATA: replay_data_cfg}

sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
