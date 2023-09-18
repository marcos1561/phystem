#pragma once

#include <vector>
#include <array>

using namespace std;

namespace ring {
    struct Data {
        vector<array<double, 2>> pos;
        vector<array<double, 2>> vel;
        vector<double> self_prop_angle;
    };

    Data init_cfg(int n, double r, double v0);
}