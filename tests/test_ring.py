import unittest
import os, yaml

from phystem.ring.simulation import Simulation
from phystem.ring import collect_pipelines
from phystem.ring.configs import *
from phystem.ring.run_config import CollectDataCfg
from phystem.core.run_config import UpdateType

current_folder = os.path.dirname(__file__)

class TestRing(unittest.TestCase):
    root_folder =  os.path.join(current_folder, "data_test/ring")

    def test_window(self):
        truth_folder = os.path.join(self.root_folder, "normal_data")
        cfg_path = os.path.join(truth_folder, "config.yaml")

        folder_path = os.path.join(self.root_folder, "test")

        with open(cfg_path, "r") as f:
            cfg = yaml.unsafe_load(f)

        run_cfg: CollectDataCfg = cfg["run_cfg"] 

        run_cfg.folder_path = folder_path
        run_cfg.num_col_windows = 20
        run_cfg.update_type = UpdateType.WINDOWS

        run_cfg.func = collect_pipelines.get_func(run_cfg.func_id)

        sim = Simulation(**cfg)
        sim.run()

        import numpy as np
        pos_truth = np.load(os.path.join(truth_folder, "pos.npy"))
        pos_test = np.load(os.path.join(folder_path, "pos.npy"))

        error = 0
        for i in range(pos_test.shape[0]):
            error += ((pos_test[i] - pos_truth[i])**2).sum() 

        print(f"pos error: {error}")
        self.assertTrue(error < 1e-5)
        # self.assertTrue((pos_test == pos_truth).all())