import unittest
import os 

from physical_system.simulation import Simulation
from physical_system.configs import *

current_folder = os.path.dirname(__file__)

class TestSimulation(unittest.TestCase):
    def test_total_run(self):
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
            folder_path=os.path.join(current_folder, "data_test/all_run/test"),
            solver_type=SolverType.CPP,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

        import numpy as np
        pos_test = np.load(os.path.join(current_folder, "data_test/all_run/test/pos.npy"))
        pos_truth = np.load(os.path.join(current_folder, "data_test/all_run/truth/pos.npy"))

        print(((pos_test - pos_truth)**2).sum())
        self.assertTrue(((pos_test - pos_truth)**2).sum() < 1e-5)

    def test_only_final(self):
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
            folder_path=os.path.join(current_folder, "data_test/only_final/test"),
            solver_type=SolverType.CPP,
            only_last=True,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

        import numpy as np
        pos_test = np.load(os.path.join(current_folder, "data_test/only_final/test/pos.npy"))
        vel_test = np.load(os.path.join(current_folder, "data_test/only_final/test/vel.npy"))
        
        pos_truth = np.load(os.path.join(current_folder, "data_test/only_final/truth/pos.npy"))
        vel_truth = np.load(os.path.join(current_folder, "data_test/only_final/truth/vel.npy"))

        print("pos error:", ((pos_test[1] - pos_truth[1])**2).sum())
        print("vel_error:", ((vel_test[1] - vel_truth[1])**2).sum())
        
        self.assertTrue((pos_test[0] == pos_truth[0]).all())
        self.assertTrue((vel_test[0] == vel_truth[0]).all())
        
        self.assertTrue(((pos_test[1] - pos_truth[1])**2).sum() < 1e-5)
        self.assertTrue(((vel_test[1] - vel_truth[1])**2).sum() < 1e-5)

    def test_only_final2(self):
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
            folder_path=os.path.join(current_folder, "data_test/only_final/test"),
            solver_type=SolverType.CPP,
            only_last=True,
        )

        sim = Simulation(create_cfg, self_propelling_cfg, space_cfg, run_cfg, seed)
        sim.run()

        import numpy as np
        pos_test = np.load(os.path.join(current_folder, "data_test/only_final/test/pos.npy"))
        vel_test = np.load(os.path.join(current_folder, "data_test/only_final/test/vel.npy"))
        
        pos_truth = np.load(os.path.join(current_folder, "data_test/only_final/truth2/pos.npy"))
        vel_truth = np.load(os.path.join(current_folder, "data_test/only_final/truth2/vel.npy"))

        print("pos error:", ((pos_test[1] - pos_truth[1])**2).sum())
        print("vel_error:", ((vel_test[1] - vel_truth[1])**2).sum())
        
        self.assertTrue((pos_test[0] == pos_truth[0]).all())
        self.assertTrue((vel_test[0] == vel_truth[0]).all())
        
        self.assertTrue(((pos_test[1] - pos_truth[1])**2).sum() < 1e-5)
        self.assertTrue(((vel_test[1] - vel_truth[1])**2).sum() < 1e-5)

class TestWindows(unittest.TestCase):
    def test_neighbor_ids(self):
        import physical_system.cpp_lib as cpp_lib
        import numpy as np

        n = 40
        size = 20
        num_cols = 5
        num_rows = num_cols

        pos = np.random.random((n, 2))*size - size/2
        pos = cpp_lib.PosVec(pos)

        wm = cpp_lib.WindowsManager(pos, num_cols, num_cols, size)

        correct_neighbors = self.get_correct_neighbors(num_cols, num_rows)
        
        test_neighbors = {tuple(key): [] for key in wm.windows_ids}
        for win_id in wm.windows_ids:
            for neighbor_id in wm.window_neighbor[win_id[0]][win_id[1]]:
                test_neighbors[tuple(win_id)].append(neighbor_id)
                test_neighbors[tuple(neighbor_id)].append(win_id)
            
        has_some_duplicate = False
        correct_size = True
        miss_correct_id = False
        for win_id, neighbors in test_neighbors.items():
            win_id = tuple(win_id)

            has_duplicate, duplicate_info = self.has_duplicates(neighbors)
            if has_duplicate:
                print(f"Erro duplicado! win_id={win_id} | duplicate={duplicate_info['dup_element']}")
                has_some_duplicate = True
                break
        
            if len(neighbors) != 8:
                print(f"Erro tamanho! win_id={win_id} | size={len(neighbors)}")
                correct_size = False
            
            for correct_id in correct_neighbors[win_id]:
                if correct_id not in neighbors:
                    miss_correct_id = True
                    print(f"Erro miss_id! miss_id={correct_id}")

        self.assertFalse(has_some_duplicate)
        self.assertTrue(correct_size)
        self.assertFalse(miss_correct_id)

    def test_correct_neighbors(self):
        correct_neighbors = self.get_correct_neighbors(4, 6)

        has_some_duplicate = False
        correct_size = True
        for win_id, neighbors in correct_neighbors.items():
            has_duplicate, duplicate_info = self.has_duplicates(neighbors)
            if has_duplicate:
                print(f"Erro duplicado! win_id={win_id} | duplicate={duplicate_info['dup_element']}")
                has_some_duplicate = True
                break
        
            if len(neighbors) != 8:
                print(f"Erro tamanho! win_id={win_id} | size={len(neighbors)}")
                correct_size = False

        self.assertFalse(has_some_duplicate)
        self.assertTrue(correct_size)

    @staticmethod
    def get_correct_neighbors(num_cols, num_rows):
        windows_ids = []
        for i in range(num_rows):
            for j in range(num_cols):
                windows_ids.append((i, j))

        correct_neighbors = {key: [] for key in windows_ids}
        
        id_moves = ((1, 0), (0, 1), (1, 1), (-1, 0), (0, -1),
            (-1, -1), (1, -1), (-1, 1))
        for id in windows_ids:
            for move in id_moves:
                row_id = (id[0] + move[0])%num_rows
                col_id = (id[1] + move[1])%num_cols
                correct_neighbors[id].append([row_id, col_id])
        
        return correct_neighbors

    @staticmethod
    def has_duplicates(list):
        info = {"dup_element": None}
        has_error = False
        for element in list:
            num_equal = 0
            for other in list:
                if other == element:
                    num_equal += 1
                
            if num_equal != 1:
                info = {"dup_element": element}
                has_error = True

        return has_error, info

if __name__ == '__main__':
    unittest.main()