#pragma once

#include <vector>
#include <array>

using namespace std;

using VecList = vector<array<double, 2>>;

class Solver {
public:
    VecList pos;

    double time;
    double dt;

public:
    Solver(int n, double delta_time);

    void update();
};