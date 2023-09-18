#pragma once

class RingCfg
{
public:
    float spring_k;
    float spring_r;
    
    float bend_k;

    float mobility;
    float relax_time;
    float vo;

    float trans_diff;
    float rot_diff;

    float exclusion_vol;
    float diameter; 

    RingCfg() {};

    RingCfg(float spring_k, float spring_r, float bend_k, float mobility, float relax_time, float vo,
        float trans_diff, float rot_diff, float exclusion_vol, float diameter) 
    : spring_k(spring_k), spring_r(spring_r), bend_k(bend_k), mobility(mobility), relax_time(relax_time), vo(vo),
    trans_diff(trans_diff), rot_diff(rot_diff), exclusion_vol(exclusion_vol), diameter(diameter) {};
};