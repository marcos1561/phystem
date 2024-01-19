#pragma once

enum class AreaPotencialType {
    format, 
    target_perimeter,
    target_area,
};

enum class RingUpdateType {
    stokes,
    periodic_borders,
};

enum class RingIntegrationType {
    euler,
    verlet,
    rk4,
};

class RingCfg
{
public:
    float spring_k;
    float spring_r;
    
    AreaPotencialType area_potencial;
    float k_bend;
    float p0;
    float area0;

    float mobility;
    float relax_time;
    float vo;

    float trans_diff;
    float rot_diff;

    float exclusion_vol;
    float diameter; 

    RingCfg() {};

    RingCfg(float spring_k, float spring_r, AreaPotencialType area_potencial, float k_bend, float p0, float area0, 
        float mobility, float relax_time, float vo, float trans_diff, float rot_diff, float exclusion_vol, 
        float diameter) 
    : spring_k(spring_k), spring_r(spring_r), area_potencial(area_potencial), k_bend(k_bend), p0(p0), area0(area0), mobility(mobility), 
    relax_time(relax_time), vo(vo), trans_diff(trans_diff), rot_diff(rot_diff), exclusion_vol(exclusion_vol), 
    diameter(diameter) {};
};
 
class StokesCfg {
public:    
    double obstacle_r;
    double obstacle_x;
    double obstacle_y;

    double create_length;
    double remove_length;

    int num_max_rings;

    StokesCfg(): num_max_rings(-1) { };
    
    StokesCfg(double obstacle_r, double obstacle_x, double obstacle_y,
        double create_length, double remove_length, int num_max_rings)
    : obstacle_r(obstacle_r), obstacle_x(obstacle_x), obstacle_y(obstacle_y), 
    create_length(create_length), remove_length(remove_length), num_max_rings(num_max_rings) { };
};

struct InPolCheckerCfg {
    int num_cols_windows;
    int update_freq;
    bool disable;
    
    InPolCheckerCfg() { };
    
    InPolCheckerCfg(int num_cols_windows, int update_freq, bool disable=false)
    : num_cols_windows(num_cols_windows), update_freq(update_freq), disable(disable) { }
};