from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import RealTimeCfg
from phystem.systems.ring import configs, utils, run_config
from phystem.systems.ring.ui.graph import graphs_cfg

cfgs = Simulation.load_cfg("data/data_full_checkpoint/config.yaml")

# cfgs["dynamic_cfg"].area_potencial = "format"

cfgs["dynamic_cfg"]

space_cfg = configs.SpaceCfg(
    height = 4*30,
    length = 6*30,
)
cfgs["space_cfg"] = space_cfg

radius = utils.get_ring_radius(cfgs["dynamic_cfg"].diameter, cfgs["creator_cfg"].num_p)
space_shape = (space_cfg.height/radius/2, space_cfg.length/radius/2)
cfgs["other_cfgs"]["stokes"] = configs.StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(space_shape[0] * space_shape[1] * 2), 
)

from math import ceil
num_cols = int(ceil(space_cfg.length/(cfgs["dynamic_cfg"].diameter*1.2)) * 0.6)
num_rows = int(ceil(space_cfg.height/(cfgs["dynamic_cfg"].diameter*1.2)) * 0.6)

num_cols_cm = int(ceil(space_cfg.length / (2.5*radius)))
num_rows_cm = int(ceil(space_cfg.height / (2.5*radius)))
cfgs["run_cfg"] = RealTimeCfg(
    int_cfg=run_config.IntegrationCfg(
            dt = 0.01,
            particle_win_cfg=run_config.ParticleWindows(
                num_cols=num_cols, num_rows=num_rows,
                update_freq=1),
            integration_type=run_config.IntegrationType.euler,
            update_type=run_config.UpdateType.STOKES,
            in_pol_checker=run_config.InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    ),
    graph_cfg=graphs_cfg.SimpleGraphCfg(begin_paused=False),
    num_steps_frame=500,
    fps=30,
)

sim = Simulation(**cfgs)
sim.run()