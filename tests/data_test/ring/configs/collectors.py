from phystem.core.run_config import CollectDataCfg, save_configs
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.configs import *
from phystem.systems.ring import utils

dynamic_cfg = RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    
    k_format=0.03,
    p0_format=3.5449077018, # Círculo
    
    k_area=2,
    p0=3.5449077018, # Círculo

    k_invasion = 8,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 12,
    adh_force = 20,
    
    relax_time=0.5,
    mobility=1,
    vo=1,
    
    trans_diff=0,
    rot_diff=0.1,
)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_particles = 15,
    r = None, angle = [], center = [],
)

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles) 

space_cfg = SpaceCfg(
    height = 7 * 2*radius,
    length = 15 * 2*radius,
)

num_ring_in_rect = utils.num_rings_in_rect(2*radius, space_cfg)
stokes_cfg = StokesCfg(
    obstacle_r  = 0.5 * space_cfg.height/2,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = 2.01 * radius,
    remove_length = 2.01 * radius,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(1.1 * num_ring_in_rect), 
)

num_cols, num_rows = utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = utils.rings_grid_shape(space_cfg, radius)

collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
    ), 
    tf=120,
    folder_path="Setar no teste",
    func="Setar no teste",
    func_cfg="Setar no teste",
)

configs = {
    "creator_cfg": creator_cfg, "dynamic_cfg": dynamic_cfg, 
    "space_cfg": space_cfg, "run_cfg": collect_data_cfg,
    "other_cfgs": {"stokes": stokes_cfg},
    "rng_seed": 238531723,
}

from pathlib import Path
save_configs(configs, f"{Path(__file__).stem}_configs")