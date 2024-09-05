import sys, os
from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.configs import *
from phystem.core.run_config import RealTimeCfg
from phystem.systems.ring.run_config import IntegrationType, IntegrationCfg, InPolCheckerCfg, UpdateType, ParticleWindows
from phystem.systems.ring.ui.graph.graphs_cfg import *
from phystem.systems.ring import utils
from phystem.gui_phystem.config_ui import UiSettings

sys.path.append(os.path.abspath('..'))
from extreme_pars import extreme_configs

ext_dynamic_cfg, ext_stokes = extreme_configs.get(align=0, den=0, force=1)
# extreme_configs.save("teste", 0, 0, 0)

dynamic_cfg: RingCfg = ext_dynamic_cfg
print("relax_time", dynamic_cfg.relax_time)

creator_cfg = CreatorCfg(
    num_rings = 0,
    num_particles = 10,
    r = None, angle = [], center = [],
)

radius = utils.get_ring_radius(dynamic_cfg.diameter, creator_cfg.num_particles) 

space_cfg = SpaceCfg(
    height = 7 * 2*radius,
    length = 20 * 2*radius,
)

num_ring_in_rect = space_cfg.max_num_inside(2*radius)
stokes_cfg = StokesCfg(
    obstacle_r  = 0.4 * space_cfg.height/2,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = 2.01 * radius,
    remove_length = 2.01 * radius,
    flux_force = ext_stokes["flux_force"], 
    obs_force = ext_stokes.get("obs-force", 23),
    num_max_rings = int(1.1 * num_ring_in_rect), 
)
print("obs_force:", stokes_cfg.obs_force)

num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(radius)
real_time_cfg = RealTimeCfg(
    int_cfg=IntegrationCfg(
        dt = 0.01,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.STOKES,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50, 4),
    ),
    num_steps_frame=100,
    fps=30,
    graph_cfg = SimpleGraphCfg(
        begin_paused=False,
        show_scatter=False,
        show_circles=True,
        circle_facecolor=True,
        scatter_kwargs={"s": 1},
        density_kwargs={"vmin": -1, "vmax":1},
        cbar_kwargs={"orientation": "horizontal", "label": "Densidade relativa"},
        ax_kwargs={"title": "t=8000"},
        cell_shape=[3, 3],
    ),
    ui_settings=UiSettings(
        always_update=False,
    ),
)

Simulation(creator_cfg, dynamic_cfg, space_cfg, real_time_cfg, other_cfgs={"stokes": stokes_cfg}).run()