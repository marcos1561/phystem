#pragma once

#include <array>
#include <vector>

using Vec2d = std::array<double, 2>;
using PosArray = std::vector<std::array<double, 2>>;

struct NumericCfg {
    double dr;
};

struct SolverCfg {
    double dt;
    PosArray pos;
    Vec2d vel;
    
    double k;
    float p_0;
    int point_id;

    NumericCfg numeric_cfg;  
};

class Solver {
public:
    PosArray pos;
    Vec2d vel;

    double dt;
    double k;
    float p_0;
    int point_id;

    NumericCfg numeric_cfg;
    Vec2d pos_numeric;
    Vec2d vel_numeric;

    double drag;

    double time;
public:
    Solver(SolverCfg cfg);    

public:
    void update();
    void update_numeric();

    double calc_area(PosArray& points);
    double calc_area_0(PosArray& points);
    double calc_perimeter(PosArray& points);

    double get_potencial(PosArray& points);

    Vec2d calc_force();
    Vec2d calc_force_numeric();
};