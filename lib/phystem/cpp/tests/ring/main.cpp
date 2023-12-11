#include <iostream>

#include "../../src/solvers/ring.h"
#include "../../src/intersections.h"
#include "creator.h"

using namespace std;

int main() {
    int n = 30;
    double size = 20;
    double r = size/6.0;
    int num_cols_windows = 4;
    double dt = 0.0001;

    auto cfg = RingCfg();
    cfg.spring_k = 1.;
    cfg.spring_r = 2;
    
    cfg.area_potencial = AreaPotencialType::target_perimeter;
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

    num_cols_windows=8;
    auto solver = Ring(data.pos, data.self_prop_angle, cfg, size, dt, num_cols_windows, 12415, 1, 0,
        InPolCheckerCfg(3, 10));

    for (int i = 0; i < 100000; i++)
    // while (true)
    {
        // solver.update_normal();
        solver.update_windows();
        auto pos = solver.pos[0][0];
        std::cout << pos[0] << ", " << pos[1] << std::endl;
        // std::cout << solver.self_prop_angle[0][0] << std::endl;
    }
    
    // for (auto pos: solver.pos) {
    //     std::cout << pos[0] << ", " << pos[1] << std::endl;
    // }
}
