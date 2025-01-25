'''
Exemplo simples de renderização em tempo real para bordas periódicas.
Esse exemplo cria os anéis nos vértices de uma grade retangular.
'''
from phystem.systems import ring
from phystem.systems.ring.ui.graph import graphs_cfg 
from phystem.systems.ring.configs import *
from phystem.systems.ring.run_config import *

num_particles = 10

dynamic_cfg = RingCfg(
    spring_k=14,
    spring_r=0.8,
    
    area_potencial="target_area",
    k_area=5,
    p0=ring.utils.equilibrium_p0(num_particles) * 1.1,

    k_invasion = 12,
    
    diameter  = 1,
    max_dist  = 1 * (1 + 0.1818),
    rep_force = 14,
    adh_force = 4,
    
    relax_time=1,
    mobility=1,
    vo=0.5,
    
    trans_diff=0.0,
    rot_diff=0.25,
)

creator_cfg = RectangularGridCfg.from_relative_density(
        num_x=4,
        num_y=4,
        rel_density=0.3,
        num_particles=num_particles,
        particle_diameter=dynamic_cfg.diameter,
        ring_radius_k = 1,
)
space_cfg = creator_cfg.get_space_cfg()

radius = ring.utils.ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles) 
num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(radius)

real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_cols,
            update_freq=1
        ),
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(
            num_col_windows=num_cols_cm, num_rows_windows=num_rows_cm, 
            update_freq=6, steps_after=4
        ),
    ),
    num_steps_frame=70,
    fps=30,
    graph_cfg=graphs_cfg.SimpleGraphCfg(
        show_scatter=False,
        show_circles=True,
    ),
)

sim = ring.Simulation(creator_cfg, dynamic_cfg, space_cfg, real_time_cfg)
sim.run()