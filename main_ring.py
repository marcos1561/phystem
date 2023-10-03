from phystem.ring.simulation import Simulation

from phystem.ring.configs import *
from phystem.ring.ui.graph import GraphCfg
from phystem.ring import collect_pipelines

from phystem.core.run_config import UpdateType, SolverType, RunType
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg

enable_force = 1
dynamic_cfg = RingCfg(
    spring_k=enable_force*4,
    spring_r=0.8,
    bend_k=1,
    exclusion_vol=enable_force*1,
    mobility=enable_force*1,
    diameter=1,
    relax_time=1,
    vo=10,
    trans_diff=1*enable_force*0.01,
    rot_diff=1*enable_force*0.01,
)

space_cfg = SpaceCfg(
    size = 20,
)

create_cfg = CreateCfg(
    n = 20,
    r = space_cfg.size/4,
    vo = dynamic_cfg.vo,
    angle=3.1415/180 * 0,
)

seed = 40028922
seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    dt = 0.001,
    num_steps_frame = 40,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles  = False,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_total  = False,
    )
)

replay_data_cfg = None
if run_type is RunType.REPLAY_DATA:
    replay_data_cfg = ReplayDataCfg(
        directory="data/ring/teste",
        num_steps_frame=1,
        frequency=0,
        graph_cfg=GraphCfg(),
        system_cfg = {
            "create_cfg": create_cfg,
            "dynamic_cfg": dynamic_cfg,
            "space_cfg": space_cfg
        },
    )

collect_data_cfg = CollectDataCfg(
    tf = 100,
    dt = 0.001,
    folder_path="data/ring/teste",
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
    path = "data/videos/teste.mp4",
    speed=1,
    fps=30, 
    dt=0.001,
    duration=5,
    tf=None,
    graph_cfg=GraphCfg(
        show_f_spring=True
    ),
)

run_type_to_cfg = {RunType.COLLECT_DATA: collect_data_cfg, RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg, RunType.REPLAY_DATA: replay_data_cfg}

sim = Simulation(create_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
