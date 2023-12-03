#pragma once

enum class AreaPotencialType {
    format, 
    target_perimeter,
    target_area,
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
 
struct InPolCheckerCfg {
    int num_cols_widows;
    int update_freq;
};