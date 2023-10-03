#pragma once

#include <vector>
#include <array>
#include <cmath>

#include "../../src/configs/self_propelling.h"
#include "../../src/solvers/self_propelling.h"

using namespace std;


double get_random() {
    return (double)rand()/(double)RAND_MAX * 2.0 - 1.0;
}

void generate_initial_state(vector<array<double, 2>> &pos, vector<array<double, 2>> &vel, double vo,
    int size, int n) {
    srand(time(0));
    for (int i = 0; i < n; i++) {
        array<double, 2> pi = {size/2.0 * get_random(), size/2.0 * get_random()};

        double angle_i = (double)rand()/(double)RAND_MAX * M_PI * 2;
        array<double, 2> vi = {vo * cos(angle_i), vo * sin(angle_i)};

        pos.push_back(pi);
        vel.push_back(vi);
    }
}

struct SolverCfg {
    SelfPropellingCfg dynamic_cfg;
    int n;
    double size;
    double dt;
    int num_cols_windows;
    int seed;
};

class SelfPropSolver : public SelfPropelling {
public:
    using SelfPropelling::SelfPropelling;

    SelfPropSolver(SolverCfg solver_cfg) {
        
    }

    void update() {
        SelfPropelling::update_windows();
    }
};