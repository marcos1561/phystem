from phystem.core.run_config import save_configs
from phystem.systems.ring.run_config import *
from phystem.systems.ring.configs import *

dynamic_cfg = RingCfg(
    num_particles=10,

    spring_k=8,
    spring_r=0.7,
    
    k_area=2,
    p0=3.8,

    diameter  = 1,
    max_dist  = 1 * (1 + 0.1),
    rep_force = 12,
    adh_force = 20,
    
    relax_time=1,
    mobility=1,
    vo=0.5,
    
    trans_diff=0,
    rot_diff=0.1,
)

creator_cfg = CreatorCfg.empty()

radius = dynamic_cfg.get_ring_radius()

space_cfg = SpaceCfg(
    height = 7 * 2*radius,
    length = 15 * 2*radius,
)

num_ring_in_rect = space_cfg.max_num_inside(2 * radius)
stokes_cfg = StokesCfg(
    obstacle_r  = 0.5 * space_cfg.height/2,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = 2.01 * radius,
    remove_length = 2.01 * radius,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(1.3 * num_ring_in_rect), 
)

num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(radius)

collect_data_cfg = CollectDataCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(
            num_cols_cm, num_rows_cm,
            update_freq=50, steps_after=3,                               
        ),
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