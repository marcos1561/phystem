from phystem.systems.szabo.simulation import Simulation
import phystem.systems.szabo.collect_pipelines as collect_pipelines
from phystem.systems.szabo.configs import *
from phystem.core.run_config import UpdateType, SolverType, ReplayDataCfg, RunType
from phystem.systems.szabo.run_config import CollectDataCfg, RealTimeCfg, SaveCfg, GraphCfg


self_propelling_cfg = SelfPropellingCfg(
    mobility = 1.,
    relaxation_time = 1.,
    nabla = 1,
    vo = 1.,
    max_repulsive_force = 30,
    max_attractive_force = 0.75,
    r_eq =  5/6,
    max_r = 1.,
)

space_cfg = SpaceCfg(
    # size = 18.2574185,
    # size = 57.73502691, # 0.3
    # size = 40.824829046, # 0.6
    size = 40, # 0.6
)

creator_cfg = CreatorCfg(
    n = 1000,
    r = space_cfg.size/2,
    type = CreateType.SQUARE,
)

seed = 40028922
# seed=None

run_type = RunType.SAVE_VIDEO

real_time_cfg = RealTimeCfg(
    dt = 0.01,
    num_windows=10,
    num_steps_frame = 10,
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
            "creator_cfg": creator_cfg,
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
    path = "./szabo.gif",
    speed=5,
    fps=30, 
    dt=0.01,
    duration=3,
    tf=None,
    graph_cfg = GraphCfg(
        show_circles=False
    ),
    num_windows=10,
    solver_type=SolverType.CPP,
    update_type=UpdateType.WINDOWS,
)

run_type_to_cfg = {RunType.COLLECT_DATA: collect_data_cfg, RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg, RunType.REPLAY_DATA: replay_data_cfg}

sim = Simulation(creator_cfg, self_propelling_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
