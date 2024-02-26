#pragma once

#include <vector>
#include <array>

using namespace std;

using Vector2d = vector<array<double, 2>>;
using Vector3d = vector<vector<array<double, 2>>>;

namespace ring {
    struct Data {
        Vector3d pos;
        Vector3d vel;
        vector<vector<double>> self_prop_angle;
    };

    Data init_cfg(int num_rings, int num_p, double r, double v0);
}