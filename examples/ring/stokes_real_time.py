'''
Exemplo simples de renderização em tempo real para o fluxo de stokes.
'''
from phystem.systems import ring
from phystem.systems.ring.ui.graph import graphs_cfg
from phystem.systems.ring.configs import *
from phystem.systems.ring.run_config import *

creator_cfg = CreatorCfg.empty(10)

dynamic_cfg = RingCfg(
    spring_k=20,
    spring_r=1*0.7,
    
    area_potencial="target_area",
    k_area=4,
    p0=ring.utils.get_equilibrium_p0(creator_cfg.num_particles),

    k_invasion = 11,
    
    diameter  = 1,
    max_dist  = 1 + 0.5*0.1,
    rep_force = 20,
    adh_force = 1,
    
    relax_time=1,
    mobility=1,
    vo=0.5,
    
    trans_diff=0.0,
    rot_diff=0.3,
)

radius = ring.utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles)

space_cfg = SpaceCfg(
    height=4 * 2*radius,
    length=15 * 2*radius,
)

stokes_cfg = StokesCfg(
    obstacle_r=space_cfg.height * 0.2,
    obstacle_x=0,
    obstacle_y=0,
    create_length=radius * 2.01,
    remove_length=radius * 2.01,
    flux_force=2, 
    obs_force=25,
    num_max_rings=int(1.5 * space_cfg.max_num_inside(2 * radius)), 
)

num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(radius)
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt=0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1
        ),
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=num_cols_cm, num_rows_windows=num_rows_cm, 
            update_freq=20*2, steps_after=10),
    ),
    num_steps_frame=70,
    fps=30,
    graph_cfg = graphs_cfg.SimpleGraphCfg(
        show_scatter=False,
        show_circles=True,
    ),
)

sim = ring.Simulation(
    creator_cfg, dynamic_cfg, space_cfg, real_time_cfg,
    other_cfgs={"stokes": stokes_cfg},
)
sim.run()