#pragma once

enum class AreaPotencialType {
    format, 
    target_perimeter,
    target_area,
    target_area_and_format,
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
    float k_area;
    float k_format;
    float p0;
    float area0;

    float k_invasion;

    float mobility;
    float relax_time;
    float vo;

    float trans_diff;
    float rot_diff;

    // float exclusion_vol;
    float diameter; 
    float max_dist;
    float rep_force;
    float adh_force;

    RingCfg() {};

    RingCfg(float spring_k, float spring_r, AreaPotencialType area_potencial, float k_area, float k_format, float p0, float area0, 
        float k_invasion, float mobility, float relax_time, float vo, float trans_diff, float rot_diff, float diameter,
        float max_dist, float rep_force, float adh_force, float flux_force)
    : spring_k(spring_k), spring_r(spring_r), area_potencial(area_potencial), k_area(k_area), k_format(k_format), 
    p0(p0), area0(area0), k_invasion(k_invasion), mobility(mobility), relax_time(relax_time), vo(vo), trans_diff(trans_diff), 
    rot_diff(rot_diff), diameter(diameter), max_dist(max_dist), rep_force(rep_force), adh_force(adh_force) {};
};
 
class StokesCfg {
public:    
    double obstacle_r;
    double obstacle_x;
    double obstacle_y;

    double create_length;
    double remove_length;

    double flux_force;

    int num_max_rings;

    StokesCfg(): num_max_rings(-1) { };
    
    StokesCfg(double obstacle_r, double obstacle_x, double obstacle_y,
        double create_length, double remove_length, double flux_force, int num_max_rings)
    : obstacle_r(obstacle_r), obstacle_x(obstacle_x), obstacle_y(obstacle_y), 
    create_length(create_length), remove_length(remove_length), flux_force(flux_force), 
    num_max_rings(num_max_rings) { };
};

struct ParticleWindowsCfg {
    /**
     * Configurações para as janelas a nível das
     * partículas.
    */
    int num_cols = 3;
    int num_rows = 3;
    int update_freq = 1;

    ParticleWindowsCfg() { };
    ParticleWindowsCfg(int num_cols, int num_rows, int update_freq)
    : num_cols(num_cols), num_rows(num_rows), update_freq(update_freq) { }
};

struct InPolCheckerCfg {
    /**
     * Configurações para o sistema anti-invasões.
    */
    int num_cols_windows;
    int num_rows_windows;
    int update_freq;
    bool disable;
    
    InPolCheckerCfg() { };
    
    InPolCheckerCfg(int num_cols_windows, int num_rows_windows, int update_freq, bool disable=false)
    : num_cols_windows(num_cols_windows), num_rows_windows(num_rows_windows), 
    update_freq(update_freq), disable(disable) { }
};