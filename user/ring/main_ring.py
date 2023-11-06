from phystem.ring.simulation import Simulation

from phystem.ring.configs import *
from phystem.ring.ui.graph import GraphCfg
from phystem.ring import collect_pipelines

from phystem.core.run_config import UpdateType, SolverType, RunType, ReplayDataCfg
from phystem.ring.run_config import RealTimeCfg, CollectDataCfg, SaveCfg

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area",
    k_bend=2,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo
    area0=53,

    exclusion_vol=1,
    diameter=1,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=0.1,
)

space_cfg = SpaceCfg(
    size = 30,
)

from math import pi
radius = 20/6 * 1.1
a = 2
create_cfg = CreateCfg(
    num_rings = 4,
    num_p = 30,
    r = radius,
    vo = dynamic_cfg.vo,
    angle=[pi/4, -3*pi/4, 3*pi/4, -pi/4],
    center=[
        [-a * radius, -a * radius], 
        [a * radius, a * radius], 
        [a * radius, -a * radius], 
        [-a * radius, a * radius], 
    ]
)

seed = 40028922
seed=None

run_type = RunType.REAL_TIME

real_time_cfg = RealTimeCfg(
    dt = 0.001/2,
    num_steps_frame = 1000,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = True,
        show_f_total  = False,
        begin_paused=False,
        cpp_is_debug=True,
    ),
    num_col_windows=30,
    update_type=UpdateType.NORMAL,
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
    update_type=UpdateType.NORMAL,
)

save_cfg = SaveCfg(
    path = "data/videos/teste2.mp4",
    speed=0.5,
    fps=60, 
    dt=0.0001,
    duration=10,
    tf=None,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
    ),
)

run_type_to_cfg = {RunType.COLLECT_DATA: collect_data_cfg, RunType.REAL_TIME: real_time_cfg, 
    RunType.SAVE_VIDEO: save_cfg, RunType.REPLAY_DATA: replay_data_cfg}

sim = Simulation(create_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
