from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.systems.ring.ui.graph import GraphCfg
from phystem.systems.ring import collect_pipelines

from phystem.core.run_config import UpdateType, SolverType, RunType
from phystem.core.run_config import RealTimeCfg, CollectDataCfg, SaveCfg, ReplayDataCfg

dynamic_cfg = RingCfg(
    spring_k=15,
    spring_r=0.7,
    
    k_area=1,
    # p0=4.828427, # Triângulo retângulo
    # p0=4.55901, # Triângulo equilátero
    # p0=4, # quadrado
    p0=3.5449077018, # Círculo

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
radius = 1.1*dynamic_cfg.diameter/(2*pi/30)
a = 1.6
creator_cfg = CreatorCfg(
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

run_type = RunType.COLLECT_DATA

real_time_cfg = RealTimeCfg(
    dt = 0.001,
    num_steps_frame = 1000,
    fps = 60,
    graph_cfg = GraphCfg(
        show_circles  = True,
        show_f_spring = False,
        show_f_vol    = False,
        show_f_area   = False,
        show_f_total  = False,
        cpp_is_debug=True,
    )
)

replay_data_cfg = None
if run_type is RunType.REPLAY_DATA:
    replay_data_cfg = ReplayDataCfg(
        root_path="data/ring/teste",
        num_steps_frame=1,
        frequency=0,
        graph_cfg=GraphCfg(),
        system_cfg = {
            "creator_cfg": creator_cfg,
            "dynamic_cfg": dynamic_cfg,
            "space_cfg": space_cfg
        },
    )

collect_data_cfg = CollectDataCfg(
    tf = 200,
    dt = 0.001,
    folder_path="data",
    func = collect_pipelines.area,
    # func_id = collect_pipelines.FuncID.state,
    # get_func= collect_pipelines.get_func,
    func_cfg = collect_pipelines.CollectPlCfg(
        only_last=False, 
    ),
    solver_type=SolverType.CPP,
    update_type=UpdateType.PERIODIC_WINDOWS,
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

sim = Simulation(creator_cfg, dynamic_cfg, space_cfg, run_cfg=run_type_to_cfg[run_type], rng_seed=seed)
sim.run()
