import numpy as np
import copy
from phystem.systems.ring import Simulation
from phystem.core.run_config import CollectDataCfg
from phystem.systems.ring.configs import RingCfg
from pathlib import Path

def main(configs: dict[str]):
    p0_circle = 3.5449077018
    p0_range = np.linspace(p0_circle*0.9, p0_circle*1.25, 15)
    
    root_path = Path("datas/explore_p0")
    root_path.mkdir(parents=True, exist_ok=True)

    np.save(root_path / "p0_range.npy", p0_range)

    dynamic_cfg: RingCfg = configs["dynamic_cfg"]
    run_cfg: CollectDataCfg = configs["run_cfg"]
    for idx, p0 in enumerate(p0_range):
        run_cfg.folder_path = root_path / str(idx)
        dynamic_cfg.p0 = float(p0)

        sim = Simulation(**copy.deepcopy(configs))
        sim.run()
