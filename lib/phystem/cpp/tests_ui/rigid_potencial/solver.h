#pragma once

#include <array>
#include <vector>

using Vec2d = std::array<double, 2>;
using PosArray = std::array<std::array<double, 2>, 5>;
using fPosArray = std::array<std::array<float, 2>, 5>;

struct NumericCfg {
    int n;
    double dr;

    NumericCfg() {}

    NumericCfg(int n, double dr): n(n), dr(dr) {}
};

struct SolverCfg {
    double dt;
    double k;
    PosArray pos;
    Vec2d vel;
    NumericCfg numeric_cfg;
};

class Solver {
public:
    PosArray pos;
    Vec2d vel;
    double k;
    double dt;

    Vec2d force;
    
    NumericCfg numeric_cfg;    
    Vec2d pos_numeric;
    Vec2d vel_numeric;
    std::vector<Vec2d> pos_check_list;
    Vec2d force_numeric;


    
    double time;

    fPosArray pos_gui;
public:
    Solver(SolverCfg cfg);    
    // Solver(PosArray pos, Vec2d vel, double k, double dt) : pos(pos), vel(vel), k(k), dt(dt) { }

public:
    void linear_dependent(Vec2d&, Vec2d&, Vec2d&, Vec2d&);
    void calc_force();
    
    double calc_potencial(Vec2d&);
    void calc_force_numeric();
    
    void update();

    void sync_pos();
};