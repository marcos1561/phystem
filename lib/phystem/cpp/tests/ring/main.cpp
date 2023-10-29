#include <iostream>

#include "../../src/solvers/ring.h"
#include "../../src/intersections.h"
#include "creator.h"

using namespace std;

int main() {
    int n = 30;
    double size = 20;
    double r = size/6.0;
    double dt = 0.0001;

    auto cfg = RingCfg();
    cfg.spring_k = 15.;
    cfg.spring_r = 0.5;
    
    cfg.k_bend = 1.;
    cfg.p0 = 3.544907;

    cfg.mobility = 1.;
    cfg.relax_time = 1.;
    cfg.vo = 10;

    cfg.trans_diff = 0.1;
    cfg.rot_diff = 0.1;

    cfg.exclusion_vol = 1.;
    cfg.diameter = 1.;

    auto data = ring::init_cfg(2, n, r, cfg.vo);

    auto solver = Ring(data.pos, data.vel, data.self_prop_angle, cfg, size, dt);

    // for (size_t i = 0; i < 1000; i++)
    while (true)
    {
        solver.update_normal();
        auto pos = solver.pos[0][0];
        std::cout << pos[0] << ", " << pos[1] << std::endl;
    }
    
    // for (auto pos: solver.pos) {
    //     std::cout << pos[0] << ", " << pos[1] << std::endl;
    // }
}
