import sys, os

from phystem.core.run_config import CollectDataCfg, CheckpointCfg, load_configs
from phystem.systems.ring import Simulation
from phystem.systems.ring.configs import RingCfg
from phystem.systems.ring.collectors import ColAutoSaveCfg
from phystem.systems.ring import utils
from pathlib import Path

import pipeline

sys.path.append(os.path.abspath('..'))
from extreme_pars import extreme_configs

is_high = [int(sys.argv[i]) for i in range(1, 4)]
root_name = sys.argv[4]

dynamic_cfg, ext_stokes = extreme_configs.get(align=is_high[0], den=is_high[1], force=is_high[2])

# Checkpoint Path
cp_path = Path("../datas/test_delta/autosave")
# cp_path = Path("datas/init_state_flux-0_5/checkpoint")
# cp_path = Path("datas/adh_1/autosave")

cp_cfgs = load_configs(cp_path / "autosave/config")
stokes_cfg = cp_cfgs["other_cfgs"]["stokes"]
creator_cfg = cp_cfgs["creator_cfg"]

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_p) 

start_x = (-75/2 - 1) * 2*radius
xlims = (start_x, start_x + 2*radius)
tf = 10#18000
run_cfg = CollectDataCfg(
    int_cfg=None,
    folder_path=f"datas/{root_name}",
    tf=tf,
    func=pipeline.collect_pipeline,
    func_cfg={
        "delta": {
            "min_num_rings": 4,  
            "wait_dist": stokes_cfg.obstacle_r,  
            "xlims": xlims,
            "start_dt": 2 * (xlims[1] - xlims[0]) / dynamic_cfg.vo,
            "check_dt": 1/2 * (xlims[1] - xlims[0]) / dynamic_cfg.vo,
        },
        "den_vel": {
            "xlims": xlims,
            "vel_dt": 2 / dynamic_cfg.vo,
            "density_dt": 2 / dynamic_cfg.vo,
            "vel_frame_dt": 0.5 / dynamic_cfg.vo,
        },
        "cr": {
            "wait_time": 0,
            "collect_time": tf, 
            "collect_dt": 1 / dynamic_cfg.vo,
        },
        "autosave_cfg": ColAutoSaveCfg(freq_dt=100),
    },
    checkpoint=CheckpointCfg(cp_path, override_cfgs=False, ignore_autosave=True),
    #checkpoint=CheckpointCfg("datas/adh_1/autosave"),
)
run_cfg.checkpoint.configs["dynamic_cfg"] = dynamic_cfg
for cfg_name, cfg_value in ext_stokes.items():
    run_cfg.checkpoint.configs["other_cfgs"]["stokes"].__setattr__(cfg_name, cfg_value)

print(f"Ring d: {2*radius}")

cfgs = Simulation.configs_from_checkpoint(run_cfg)
cfgs["dynamic_cfg"] = dynamic_cfg

Simulation(**cfgs).run()
