#include <iostream>
#include <cmath>
#include <vector>

#include "solver.h"

Solver::Solver(SolverCfg cfg) : pos(cfg.pos), vel(cfg.vel), k(cfg.k), dt(cfg.dt), numeric_cfg(cfg.numeric_cfg) { 
    for (std::size_t i = 0; i < pos.size(); i++) {   
        pos_gui[i][0] = pos[i][0];    
        pos_gui[i][1] = pos[i][1];    
    }

    pos_numeric[0] = pos[2][0];
    pos_numeric[1] = pos[2][1];
    vel_numeric[0] = vel[0];
    vel_numeric[1] = vel[1];

    double d_theta = (2.0*M_PI)/ ((double)numeric_cfg.n);
    double theta = 0.0;
    pos_check_list = std::vector<Vec2d>(numeric_cfg.n);
    for (auto& pos_check : pos_check_list) {
        pos_check[0] = numeric_cfg.dr * cos(theta); 
        pos_check[1] = numeric_cfg.dr * sin(theta);
        theta += d_theta;
    }

    time = 0;
}

double calc_norm(Vec2d &a) {
    return sqrt(a[0]*a[0] + a[1]*a[1]);
}

void calc_unit(Vec2d &unitary, Vec2d &a, Vec2d &b) {
    double dx = b[0] - a[0];
    double dy = b[1] - a[1];
    double comp = sqrt(dx*dx + dy*dy);

    if (comp == 0) {
        unitary[0] = 0.0;
        unitary[1] = 1.0;
        return;
    }

    unitary[0] = dx/comp;
    unitary[1] = dy/comp;
}

double calc_dist(Vec2d& a, Vec2d& b) {
    double dx = b[0] - a[0];
    double dy = b[1] - a[1];
    double comp = sqrt(dx*dx + dy*dy);

    return comp;
}

double dot_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[0] + a[1] * b[1];
}

double cross_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[1] - a[1] * b[0];
}

Vec2d calc_sum(Vec2d &a, Vec2d& b) {
    return {a[0] + b[0], a[1] + b[1]};
}

void Solver::linear_dependent(Vec2d& a_unit, Vec2d& b_unit, Vec2d& c_unit, Vec2d& d_unit) {
    double dist1 = calc_dist(pos[1], pos[2]);
    double dist2 = calc_dist(pos[2], pos[3]);

    Vec2d f_direction = {-b_unit[1], b_unit[0]};

    double sin_1 = cross_prod(a_unit, b_unit);
    double sin_2 = cross_prod(c_unit, d_unit);

    double f_intensity = -sin_1 * 1.0 / dist1 - sin_2 * 1.0 / dist2;

    force[0] = f_direction[0] * f_intensity; 
    force[1] = f_direction[1] * f_intensity; 
}

double Solver::calc_potencial(Vec2d& p) {
    Vec2d a_unit; 
    Vec2d b_unit; 
    Vec2d c_unit;
    Vec2d d_unit;

    calc_unit(a_unit, pos[0], pos[1]); 
    calc_unit(b_unit, pos[1], p); 
    calc_unit(c_unit, p, pos[3]); 
    calc_unit(d_unit, pos[3], pos[4]); 

    return k/2.0 * (cross_prod(a_unit, b_unit) + cross_prod(b_unit, c_unit) + cross_prod(c_unit, d_unit));
}

void Solver::calc_force_numeric() {
    double phi = calc_potencial(pos_numeric);

    Vec2d p_i = pos_numeric;
    p_i[0] += numeric_cfg.dr;
    double phi_x = calc_potencial(p_i);
    
    p_i = pos_numeric;
    p_i[1] += numeric_cfg.dr;
    double phi_y = calc_potencial(p_i);

    force_numeric[0] = -(phi_x - phi)/numeric_cfg.dr; 
    force_numeric[1] = -(phi_y - phi)/numeric_cfg.dr; 

    // double current_p = calc_potencial(pos_numeric);

    // Vec2d& dr = pos_check_list[0];
    // auto p_check = calc_sum(pos_numeric, dr);
    // double gradient = (calc_potencial(p_check) - current_p) / numeric_cfg.dr;
    // for (auto& dr_i: pos_check_list) {
    //     p_check = calc_sum(pos_numeric, dr_i);
    //     double gradient_check = (calc_potencial(p_check) - current_p) / numeric_cfg.dr;
        
    //     if (gradient_check > gradient) {
    //         gradient = gradient_check;
    //         dr = dr_i;
    //     }
    // }

    // Vec2d force_dir = {-dr[0]/numeric_cfg.dr, -dr[1]/numeric_cfg.dr};

    // force_numeric[0] = gradient * force_dir[0]; 
    // force_numeric[1] = gradient * force_dir[1]; 
}


void Solver::calc_force() {
    Vec2d a_unit; 
    Vec2d b_unit; 
    Vec2d c_unit;
    Vec2d d_unit;

    calc_unit(a_unit, pos[0], pos[1]); 
    calc_unit(b_unit, pos[1], pos[2]); 
    calc_unit(c_unit, pos[2], pos[3]); 
    calc_unit(d_unit, pos[3], pos[4]); 
    
    if (fabs(dot_prod(b_unit, c_unit)) > 0.999) {
        linear_dependent(a_unit, b_unit, c_unit, d_unit);
        return;
    }
    
    double cos_theta = dot_prod(a_unit, b_unit);
    // double sin_theta = 1 - sqrt(1 - cos_theta*cos_theta);  
    double sin_theta = cross_prod(a_unit, b_unit);

    Vec2d c_rotated;
    c_rotated[0] = cos_theta * c_unit[0] + sin_theta * c_unit[1];
    c_rotated[1] = -sin_theta * c_unit[0] + cos_theta * c_unit[1];

    Vec2d a_rot_90 = {-a_unit[1], a_unit[0]};

    double common_term = dot_prod(a_rot_90, c_rotated);  

    // double cos_theta_2 = dot_prod(c_unit, d_unit);
    // double sin_theta_2 = 1 - sqrt(1- cos_theta_2*cos_theta_2);
    double sin_theta_2 = cross_prod(c_unit, d_unit);

    double deriv_1 = k / 2.0 * (-sin_theta + common_term);
    double deriv_2 = k / 2.0 * (-sin_theta_2 + common_term);

    Vec2d b_rot_90 = {-b_unit[1], b_unit[0]};
    Vec2d c_rot_90 = {-c_unit[1], c_unit[0]};

    double direction_check1 = dot_prod(b_rot_90, c_unit);
    double direction_check2 = dot_prod(c_rot_90, b_unit);

    double sign1 = 1.0;
    double sign2 = 1.0;
    
    if (direction_check1 < 0)
        sign1 = -1.0;
    
    if (direction_check2 < 0) 
        sign2 = -1.0;

    Vec2d s1 = {sign1 * c_unit[0], sign1 * c_unit[1]};
    Vec2d s2 = {sign2 * b_unit[0], sign2 * b_unit[1]};

    double f_denominator = cross_prod(s1, s2);

    force[0] = (deriv_2 * s1[1] - deriv_1 * s2[1]) / (-f_denominator);
    force[1] = (deriv_2 * s1[0] - deriv_1 * s2[0]) / f_denominator;
}

void Solver::update() {
    double drag = 2;

    calc_force();

    vel[0] += (force[0] - vel[0] * drag) * dt;
    vel[1] += (force[1] - vel[1] * drag) * dt;

    pos[2][0] += vel[0] * dt;
    pos[2][1] += vel[1] * dt;
    
    calc_force_numeric();

    std::cout << "analytical: " << calc_norm(force) << " | " << force[1]/force[0] << std::endl;
    std::cout << "numeric   : " << calc_norm(force_numeric) << " | " << force_numeric[1]/force_numeric[0] << std::endl;
    std::cout << "===========" << std::endl;

    vel_numeric[0] += (force_numeric[0] - vel_numeric[0] * drag) * dt;
    vel_numeric[1] += (force_numeric[1] - vel_numeric[1] * drag) * dt;

    pos_numeric[0] += vel_numeric[0] * dt;
    pos_numeric[1] += vel_numeric[1] * dt;

    sync_pos();
    time += dt;
}

void Solver::sync_pos() {
    for (std::size_t i = 0; i < pos_gui.size(); i++)
    {
        if (i == 2)
            continue;

        pos[i][0] = pos_gui[i][0];
        pos[i][1] = pos_gui[i][1];
    }  
}
