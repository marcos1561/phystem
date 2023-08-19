import os

from physical_system.configs import *
from physical_system.simulation import Simulation

current_folder = os.path.dirname(__file__)

def generate_total_run_data():
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

        create_cfg = CreateCfg(
            n = 100,
            r = space_cfg.size/2,
            type = CreateType.SQUARE,
        )

        seed = 40028922

        run_cfg = CollectDataCfg(
            tf = 0.05 * 1000,
            dt = 0.05,
            folder_path=os.path.join(current_folder, "all_run/truth"),
            solver_type=SolverType.CPP,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

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

        create_cfg = CreateCfg(
            n = 200,
            r = space_cfg.size/2,
            type = CreateType.SQUARE,
        )

        seed = 40028922

        run_cfg = CollectDataCfg(
            tf = 100,
            dt = 0.05,
            folder_path=os.path.join(current_folder, "only_final/truth"),
            solver_type=SolverType.CPP,
            only_last=True,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
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
            size = 10,
        )

        create_cfg = CreateCfg(
            n = 5,
            r = space_cfg.size/2,
            type = CreateType.SQUARE,
        )

        seed = 40028922

        run_cfg = CollectDataCfg(
            tf = 100,
            dt = 0.05,
            folder_path=os.path.join(current_folder, "only_final/truth2"),
            solver_type=SolverType.CPP,
            only_last=True,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

# generate_total_run_data()
# generate_final_run_data_1()
# generate_final_run_data_2()
