from phystem.ring.simulation import Simulation

from phystem.ring.configs import *
from phystem.ring.ui.graph import GraphCfg
from phystem.ring import collect_pipelines

from phystem.core.run_config import UpdateType, SolverType, RunType
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg

dynamic_cfg = RingCfg(
    spring_k=15,
    spring_r=0.5,
    
    k_bend=1,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo

    exclusion_vol=1,
    diameter=1,
    
    relax_time=1,
    mobility=1,
    vo=10,
    
    trans_diff=0.1,
    rot_diff=0.1,
)

space_cfg = SpaceCfg(
    size = 20,
)

create_cfg = CreateCfg(
    n = 30,
    r = space_cfg.size/4,
    vo = dynamic_cfg.vo,
    angle=3.1415/180 * 0,
)

seed = 40028922
seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    dt = 0.0001,
    num_steps_frame = 1000,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles  = False,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
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
