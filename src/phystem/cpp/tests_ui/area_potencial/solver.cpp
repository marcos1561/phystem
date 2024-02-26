#include <iostream>
#include <cmath>
#include <vector>

#include "solver.h"

double dot_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[0] + a[1] * b[1];
}

double cross_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[1] - a[1] * b[0];
}

double vector_dist(Vec2d& a, Vec2d& b) {
    double dx = b[0] - a[0];
    double dy = b[1] - a[1];
    double comp = sqrt(dx*dx + dy*dy);

    return comp;
}

Solver::Solver(SolverCfg cfg) : pos(cfg.pos), vel(cfg.vel), dt(cfg.dt), k(cfg.k), 
    p_0(cfg.p_0), point_id(cfg.point_id), numeric_cfg(cfg.numeric_cfg) { 
    time = 0;
    
    pos_numeric = pos[point_id];
    vel_numeric = vel;

    // std::cout << calc_perimeter() << std::endl;
    // std::cout << 0.6 + 2 * 2 * 0.3 << std::endl;
    // std::cout << 0.6 * 4 << std::endl;
}
 
double Solver::get_potencial(PosArray& points) {
    double area = calc_area(points);
    double perimeter = calc_perimeter(points);

    double area_0 = pow(perimeter/p_0, 2);

    return k/2.0 * pow(area - area_0, 2);
}

double Solver::calc_perimeter(PosArray& points) {
    double perimeter = 0.0;

    for (size_t i = 0; i < points.size()-1; i++)
    {
        perimeter += vector_dist(points[i], points[i+1]);
    }
    int i = points.size() - 1;
    perimeter += vector_dist(points[i], points[0]);

    return perimeter;
}

double Solver::calc_area(PosArray& points) {
    double area = 0.0;

    for (size_t i = 0; i < points.size()-1; i++) {
        auto& p1 = points[i];
        auto& p2 = points[i+1];
        area += cross_prod(p1, p2);
    }
    int i = points.size() - 1;
    auto& p1 = points[i];
    auto& p2 = points[0];
    area += cross_prod(p1, p2);

    return area / 2.0;
}

double Solver::calc_area_0(PosArray& points) {
    double p = calc_perimeter(points);
    return (p/p_0) * (p/p_0);
}

Vec2d Solver::calc_force() {
    int id = pos.size() - 1;
    if (point_id != 0)
        id = point_id - 1;
    auto& v1 = pos[id];
    
    id = 0;
    if (point_id != (pos.size() - 1))
        id = point_id + 1;
    auto& v2 = pos[id];

    auto& point = pos[point_id]; 

    double area = calc_area(pos);
    double perimeter = calc_perimeter(pos);

    double d1 = vector_dist(v1, pos[point_id]);
    double d2 = vector_dist(v2, pos[point_id]);

    double delta_area = area - (perimeter/p_0) * (perimeter/p_0);

    double area_0_deriv_x =  2.0 * perimeter / (p_0*p_0) * ((v1[0] - point[0]) / d1 +  (v2[0] - point[0]) / d2);
    double area_0_deriv_y =  2.0 * perimeter / (p_0*p_0) * ((v1[1] - point[1]) / d1 +  (v2[1] - point[1]) / d2);
    
    double gradient_x = k * delta_area * ((v2[1] - v1[1])/2.0 + area_0_deriv_x);
    double gradient_y = k * delta_area * (-(v2[0] - v1[0])/2.0 + area_0_deriv_y);

    return {-gradient_x, -gradient_y};
}

void Solver::update_numeric() {
    PosArray points = pos;
    
    points[point_id] = pos_numeric;
    double phi = get_potencial(points);

    points[point_id] = pos_numeric;
    points[point_id][0] += numeric_cfg.dr;
    double phi_x = get_potencial(points);
    
    points[point_id] = pos_numeric;
    points[point_id][1] += numeric_cfg.dr;
    double phi_y = get_potencial(points);

    Vec2d force = {-(phi_x - phi)/numeric_cfg.dr, -(phi_y - phi)/numeric_cfg.dr};

    vel_numeric[0] += (force[0] - vel_numeric[0] * drag) * dt;
    vel_numeric[1] += (force[1] - vel_numeric[1] * drag) * dt;

    pos_numeric[0] += vel_numeric[0] * dt;
    pos_numeric[1] += vel_numeric[1] * dt;
}

void Solver::update() {
    drag = 1.0;

    auto force = calc_force();

    vel[0] += (force[0] - vel[0] * drag) * dt;
    vel[1] += (force[1] - vel[1] * drag) * dt;

    pos[point_id][0] += vel[0] * dt;
    pos[point_id][1] += vel[1] * dt;

    update_numeric();
    
    time += dt;
}
