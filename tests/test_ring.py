import unittest
import os, yaml
from copy import deepcopy
import shutil
from pathlib import Path

from phystem.core.run_config import CheckpointCfg, load_configs

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring import collect_pipelines, utils
from phystem.systems.ring.collectors import StateSaver

from phystem.systems.ring.configs import *
from phystem.systems.ring.run_config import IntegrationCfg, UpdateType, ParticleWindows
from phystem.core.run_config import CollectDataCfg

current_folder = Path(os.path.dirname(__file__))

class TestRing(unittest.TestCase):
    root_data_path = current_folder / "data_test/ring"

    def test_window(self):
        truth_folder = self.root_data_path / "test_windows"
        cfg_path = truth_folder / "config.yaml"

        folder_path = self.root_data_path / "test"

        with open(cfg_path, "r") as f:
            cfg = yaml.unsafe_load(f)

        run_cfg: CollectDataCfg = cfg["run_cfg"] 
        int_cfg: IntegrationCfg = run_cfg.int_cfg

        run_cfg.folder_path = folder_path
        
        # num_cols = int(ceil(size/(diameter*1.2)) * 0.6)
        num_cols, num_rows = utils.particle_grid_shape(cfg["space_cfg"], cfg["dynamic_cfg"].max_dist)
        int_cfg.particle_win_cfg = ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq= 1
        )
        int_cfg.update_type = UpdateType.PERIODIC_WINDOWS

        run_cfg.func = collect_pipelines.get_func(run_cfg.func_id)

        sim = Simulation(**cfg)
        sim.run()

        import numpy as np
        pos_truth = np.load(truth_folder / "pos.npy")
        pos_test = np.load(folder_path / "pos.npy")

        error = 0
        for i in range(pos_test.shape[0]):
            error += ((pos_test[i] - pos_truth[i])**2).sum() 

        print(f"pos error: {error}")
        self.assertTrue(error < 1e-5)
        # self.assertTrue((pos_test == pos_truth).all())

    def test_checkpoint(self):
        def func(sim: Simulation, cfg):
            before_checkpoint_path = self.root_data_path / "before_checkpoint"
            after_checkpoint_path = self.root_data_path / "after_checkpoint"

            state_saver = StateSaver(sim.solver, before_checkpoint_path, sim.configs)

            solver = sim.solver
            while solver.time < 50:
                solver.update()
            
            state_saver.save()

            configs2 = deepcopy(sim.configs)
            configs2["run_cfg"].checkpoint = CheckpointCfg(before_checkpoint_path)
            sim2 = Simulation(**configs2)
            state_saver2 = StateSaver(sim2.solver, after_checkpoint_path, sim2.configs)
            state_saver2.save()

            state_data, metadada = StateSaver.load(before_checkpoint_path)
            state_data2, metadada2 = StateSaver.load(after_checkpoint_path)

            def square_diff(a, b):
                return ((a - b)**2).sum()

            self.assertAlmostEqual(square_diff(state_data.pos, state_data2.pos), 0, msg="pos diff")
            self.assertAlmostEqual(square_diff(state_data.uids, state_data2.uids), 0, msg="uids diff")
            self.assertAlmostEqual(square_diff(state_data.ids, state_data2.ids), 0, msg="ids diff")
            self.assertAlmostEqual(square_diff(state_data.angle, state_data2.angle), 0, msg="angle diff")

            shutil.rmtree(before_checkpoint_path)
            shutil.rmtree(after_checkpoint_path)

        configs = load_configs(self.root_data_path / "configs", "checkpoint_configs")

        run_cfg: CollectDataCfg = configs["run_cfg"]
        run_cfg.func = func
        
        Simulation(**configs).run()


class TestWindows(unittest.TestCase):
    def test_neighbor_ids(self):
        import phystem.cpp_lib as cpp_lib
        import numpy as np

        n = 40
        num_p = 10
        
        height = 20
        length = 10
        
        num_cols = 5
        num_rows = num_cols

        pos = np.random.random((n, num_p, 2))*2 - 1

        pos[:,:,0] *= length/2
        pos[:,:,1] *= height/2
        
        from phystem.cpp_lib.data_types import PosVec
        from phystem.cpp_lib.data_types import Vector3d 
        
        pos = Vector3d(PosVec(ring) for ring in pos)

        # wm = cpp_lib.managers.WindowsManager(pos, num_cols, num_cols, size)
        space_info = cpp_lib.managers.SpaceInfo(height, length, [0, 0])
        wm = cpp_lib.managers.WindowsManagerRing(pos, num_cols, num_cols, space_info)

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

