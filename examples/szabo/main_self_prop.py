from phystem.systems.szabo.simulation import Simulation
import phystem.systems.szabo.collect_pipelines as collect_pipelines
from phystem.systems.szabo.configs import *
from phystem.core.run_config import SolverType, ReplayDataCfg, RunType
from phystem.core.run_config import CollectDataCfg, RealTimeCfg, SaveCfg
from phystem.systems.szabo.run_config import GraphCfg, IntegrationCfg, UpdateType

self_propelling_cfg = SelfPropellingCfg(
    r_eq =  1,
    max_r = 1 + 0.1,
    max_repulsive_force = 30,
    max_attractive_force = 0.75,
    
    mobility = 1.,
    relaxation_time = 1.,
    vo = 1,
    
    nabla = 0.3,
)

space_cfg = SpaceCfg(
    # size = 18.2574185,
    # size = 57.73502691, # 0.3
    # size = 40.824829046, # 0.6
    size = 40, # 0.6
)

creator_cfg = CreatorCfg(
    n = 50,
    r = space_cfg.size/2,
    type = CreateType.SQUARE,
)

# seed = 40028922
seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    int_cfg= IntegrationCfg(
        dt = 0.01,
        num_col_windows=30,
        solver_type = SolverType.CPP,
        update_type = UpdateType.NORMAL,
    ),
    num_steps_frame = 10,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles=False),
)

replay_data_cfg = None
if run_type is RunType.REPLAY_DATA:
    replay_data_cfg = ReplayDataCfg(
        root_path="data/self_propelling/teste",
        num_steps_frame=3,
        frequency=0,
        system_cfg = {
            "creator_cfg": creator_cfg,
            "dynamic_cfg": self_propelling_cfg,
            "space_cfg": space_cfg
        },
    )

# collect_data_cfg = CollectDataCfg(
#     int_cfg= IntegrationCfg(
#         dt = 0.01,
#         num_col_windows=10,
#         solver_type = SolverType.CPP,
#         update_type = UpdateType.WINDOWS,
#     ),
#     tf = 100,
#     folder_path="data/self_propelling/teste",
#     func = collect_pipelines.state,
#     # func_id = collect_pipelines.FuncID.state,
#     # get_func= collect_pipelines.get_func,
#     func_cfg = collect_pipelines.CollectPlCfg(
#         only_last=False, 
#     ),
# )

save_cfg = SaveCfg(
    int_cfg= IntegrationCfg(
        dt = 0.01,
        num_col_windows=10,
        solver_type = SolverType.CPP,
        update_type = UpdateType.WINDOWS,
    ),
    path = "./szabo.gif",
    speed=5,
    fps=30, 
    duration=3,
    tf=None,
    graph_cfg = GraphCfg(
        show_circles=False
    ),
)

run_type_to_cfg = {
    # RunType.COLLECT_DATA: collect_data_cfg, 
    RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg, 
    RunType.REPLAY_DATA: replay_data_cfg,
}

sim = Simulation(creator_cfg, self_propelling_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
