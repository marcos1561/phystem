import os

from phystem.systems.szabo.configs import *
from phystem.systems.szabo.run_config import CollectDataCfg
from phystem.core.run_config import SolverType, UpdateType
from phystem.systems.szabo.simulation import Simulation
from phystem.systems.szabo.collect_pipelines import CollectPlCfg
from phystem.systems.szabo import collect_pipelines

current_folder = os.path.dirname(__file__)

def generate_final_run_data_1():
        self_propelling_cfg = SelfPropellingCfg(
            mobility = 1.,
            relaxation_time = 1.,
            nabla = 2 ,
            vo = 1.,
            max_repulsive_force = 1.,
            max_attractive_force = 1.,
            r_eq =  5/6,
            max_r = 1.,
        )

        space_cfg = SpaceCfg(
            size = 30,
        )

        creator_cfg = CreatorCfg(
            n = 200,
            r = space_cfg.size/2,
            type = CreateType.SQUARE,
        )

        seed = 40028922

        run_cfg = CollectDataCfg(
            tf = 20,
            dt = 0.05,
            num_windows=15,
            folder_path=os.path.join(current_folder, "only_final/truth"),
            func_id=collect_pipelines.FuncID.state,
            get_func=collect_pipelines.get_func,
            func_cfg=CollectPlCfg(only_last=True),
            solver_type=SolverType.CPP,
            update_type=UpdateType.NORMAL,
        )

        sim = Simulation(creator_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

def generate_final_run_data_2():
        self_propelling_cfg = SelfPropellingCfg(
            mobility = 1.,
            relaxation_time = 1.,
            nabla = 2 ,
            vo = 1.,
            max_repulsive_force = 1.,
            max_attractive_force = 1.,
            r_eq =  5/6,
            max_r = 1.,
        )

        space_cfg = SpaceCfg(
            size = 11,
        )

        creator_cfg = CreatorCfg(
            n = 10,
            r = space_cfg.size/2,
            type = CreateType.SQUARE,
        )

        seed = 40028922

        run_cfg = CollectDataCfg(
            tf = 100,
            dt = 0.01,
            num_windows=10,
            folder_path=os.path.join(current_folder, "only_final/truth2"),
            func_id=collect_pipelines.FuncID.state,
            get_func=collect_pipelines.get_func,
            func_cfg=CollectPlCfg(only_last=True),
            solver_type=SolverType.CPP,
            update_type=UpdateType.NORMAL,
        )

        sim = Simulation(creator_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

generate_final_run_data_1()
generate_final_run_data_2()
