#include <iostream>

#include "../../src/solvers/ring.h"
#include "../../src/intersections.h"
#include "creator.h"

using namespace std;

int main() {
    int n = 30;
    double size = 60;
    double r = 20/6.0;
    int num_cols_windows = 4;
    double dt = 0.0001;

    StokesCfg stokes_cfg;
    stokes_cfg.obstacle_r = size * 0.5 * 0.5;
    stokes_cfg.obstacle_x = 0.0;
    stokes_cfg.obstacle_y = 0.0;
    stokes_cfg.create_length = 2.5 * r;
    stokes_cfg.remove_length = 0.0;
    stokes_cfg.num_max_rings = 100;

    std::cout << stokes_cfg.num_max_rings << std::endl;

    auto cfg = RingCfg();
    cfg.spring_k = 1.;
    cfg.spring_r = 2;
    
    cfg.area_potencial = AreaPotencialType::target_area;
    cfg.k_bend = 1.;
    cfg.p0 = 3.544907;
    cfg.area0 = 10;

    cfg.mobility = 1.;
    cfg.relax_time = 1.;
    cfg.vo = 10;

    cfg.trans_diff = 0.1;
    cfg.rot_diff = 0.1;

    cfg.exclusion_vol = 1.;
    cfg.diameter = 1.;

    auto data = ring::init_cfg(2, n, r, cfg.vo);
    data.pos = Vector3d(0);
    data.self_prop_angle = std::vector<vector<double>>(0);

    num_cols_windows=8;
    auto solver = Ring(data.pos, data.self_prop_angle, n, cfg, size, size, dt, num_cols_windows, 12415, 1, 
        RingUpdateType::stokes, RingIntegrationType::euler, stokes_cfg, InPolCheckerCfg(3, 10));

    // for (int i = 0; i < 10; i++)
    while (true)
    {
        // solver.update_normal();
        solver.update_stokes();
        auto pos = solver.pos[0][0];
        std::cout << pos[0] << ", " << pos[1] << std::endl;
        std::cout << "Num active: " << solver.num_active_rings << std::endl;
        // std::cout << solver.self_prop_angle[0][0] << std::endl;
    }
    
    // for (auto pos: solver.pos) {
    //     std::cout << pos[0] << ", " << pos[1] << std::endl;
    // }
}
