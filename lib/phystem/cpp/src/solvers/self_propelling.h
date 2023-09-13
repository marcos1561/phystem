#include <cmath>
#include <vector>
#include <array>
#include <iostream>
#include <cstdlib> 

#include "../config.h"
#include "../rng_manager.h"
#include "../windows_manager.h"

using namespace std;

class SelfPropelling {
private:
    double size;
    double dt;

    // Self propelling config
    SelfPropellingCfg propelling_cfg;
    double nabla;
    double relaxation_time;
    
    double mobility;
    double vo;
    
    double max_repulsive_force;
    double max_attractive_force;
    double r_eq;
    double max_r;
    //
    
    vector<array<double, 2>> sum_forces_matrix;
    
    WindowsManager windows_manager;
public:
    int n;

    vector<array<double, 2>> pos;
    vector<array<double, 2>> vel;
    vector<array<double, 2>> propelling_vel;
    vector<double> propelling_angle;
        
    vector<vector<double*>> py_pos = vector<vector<double*>>(2);
    vector<vector<double*>> py_vel = vector<vector<double*>>(2);
    vector<vector<double*>> py_propelling_vel = vector<vector<double*>>(2);

    // Debug
    RngManager rng_manager;
    double random_number;
    int superposition_count;

    vector<array<int, 2>> pairs_computed;

    vector<array<double, 2>> sum_forces_matrix_debug;    
    //  

    SelfPropelling(vector<array<double, 2>> &pos0, vector<array<double, 2>> &vel0, 
        SelfPropellingCfg propelling_cfg, double size, double dt, int num_col_windows, double seed=-1.) 
    : size(size), dt(dt), propelling_cfg(propelling_cfg), pos(pos0), vel(vel0)
    {
        if (seed != -1.)
            srand(seed);
        else
            srand(time(0));

        n = pos0.size();
        
        windows_manager = WindowsManager(&pos, num_col_windows, num_col_windows, size);

        initialize_propelling();

        for (size_t i=0; i < pos.size(); i ++) {
            py_pos[0].push_back(&pos[i][0]);
            py_pos[1].push_back(&pos[i][1]);

            py_vel[0].push_back(&vel[i][0]);
            py_vel[1].push_back(&vel[i][1]);

            py_propelling_vel[0].push_back(&propelling_vel[i][0]);
            py_propelling_vel[1].push_back(&propelling_vel[i][1]);
        }        

        // Debug
        rng_manager = RngManager(n);
        //
    }

    void initialize_propelling() {
        mobility = propelling_cfg.mobility;
     
        relaxation_time = propelling_cfg.relaxation_time;
        vo = propelling_cfg.vo;
        nabla = propelling_cfg.nabla;

        max_repulsive_force =  propelling_cfg.max_repulsive_force;
        max_attractive_force =  propelling_cfg.max_attractive_force;
        r_eq =  propelling_cfg.r_eq;
        max_r =  propelling_cfg.max_r;

        sum_forces_matrix = vector<array<double, 2>>(n, {0., 0.});
        
        // Debug
        sum_forces_matrix_debug = vector<array<double, 2>>(n, {0., 0.});
        //

        propelling_angle = vector<double>(n);
        propelling_vel = vector<array<double, 2>>(n, {0., 0.});
        for (int i=0; i < n; i++) {
            double angle = 2.0f * M_PI * (double)rand()/(double)RAND_MAX;
            propelling_angle[i] = angle;
            propelling_vel[i][0] = cos(angle);
            propelling_vel[i][1] = sin(angle);
        }
    }

    void calc_force(int p_id, int other_id) {
        // Debug
        // pairs_computed.push_back({p_id, other_id});
        // pairs_computed.push_back({other_id, p_id});
        //

        auto &other = pos[other_id]; 
        auto &pos_i = pos[p_id]; 

        double dx = other[0] - pos_i[0];
        double dy = other[1] - pos_i[1];

        // NOTE: Quando o espaço não for um quadrado, é necessário
        // usar box_width para o dx e box_height para o dy.         
        if (abs(dx) > size * 0.5)
            dx -= copysign(size, dx);

        if (abs(dy) > size * 0.5)
            dy -= copysign(size, dy);

        double dist = sqrt(dx*dx + dy*dy);

        if (dist > max_r) {
            return;
        }

        if (dist < 1e-6) {
            // Debug
            superposition_count += 1;
            //

            sum_forces_matrix[p_id][0] += propelling_cfg.max_repulsive_force;
            sum_forces_matrix[p_id][1] += 0;

            sum_forces_matrix[other_id][0] += -propelling_cfg.max_repulsive_force;
            sum_forces_matrix[other_id][1] += 0;
            return;
        }

        double scalar;
        if (dist < r_eq) {
            scalar = max_repulsive_force * (dist - r_eq) / r_eq;
        } else {
            scalar = max_attractive_force * (dist - r_eq) / (max_r - r_eq);
        }

        sum_forces_matrix[p_id][0] += dx/dist * scalar;
        sum_forces_matrix[p_id][1] += dy/dist * scalar;

        sum_forces_matrix[other_id][0] += -dx/dist * scalar;
        sum_forces_matrix[other_id][1] += -dy/dist * scalar;

        return;
    }

    void update_windows() {
        // Debug
        rng_manager.update();
        // pairs_computed = vector<array<int, 2>>();
        
        superposition_count = 0;
        //  
        
        windows_manager.update_window_members();

        for (auto win_id: windows_manager.windows_ids) {
            auto & window = windows_manager.windows[win_id[0]][win_id[1]];
            auto & neighbors = windows_manager.window_neighbor[win_id[0]][win_id[1]];
            int windows_cap = windows_manager.capacity[win_id[0]][win_id[1]];
            
            for (int i=0; i < windows_cap; i++) {
                auto p_id = window[i];

                for (int j = i+1; j < windows_cap; j ++) {
                    auto other_id = window[j];
                    calc_force(p_id, other_id);
                }

                for (auto neigh_id : neighbors) {
                    auto & neigh_window = windows_manager.windows[neigh_id[0]][neigh_id[1]];
                    int neigh_window_cap = windows_manager.capacity[neigh_id[0]][neigh_id[1]];

                    for (int j = 0; j < neigh_window_cap; j ++) {
                        auto other_id = neigh_window[j];
                        calc_force(p_id, other_id);
                    }
                }
            }
        }

        for (int i=0; i < n; i++) {
            pos[i][0] += dt * vel[i][0];
            pos[i][1] += dt * vel[i][1];
            
            // random_number = (double)rand();
            // Debug
            random_number = (double)rng_manager.get_random_num(i);
            //

            double noise = 1. / (2. * sqrt(dt)) * (2. * random_number/(double)RAND_MAX - 1.);
            // double noise = 1. / (2. * sqrt(0.05)) * (2. * random_number/(double)RAND_MAX - 1.);
            
            double random_angle = noise * nabla;
            double speed = sqrt(vel[i][0]*vel[i][0] + vel[i][1]*vel[i][1]);
            double cross_prod = propelling_vel[i][0] * vel[i][1]/speed - propelling_vel[i][1] * vel[i][0]/speed;
            double angle_derivate = 1.f / relaxation_time * asin(cross_prod) + random_angle;  

            propelling_angle[i] += angle_derivate * dt;

            vel[i][0] = vo * propelling_vel[i][0] + mobility * sum_forces_matrix[i][0];
            vel[i][1] = vo * propelling_vel[i][1] + mobility * sum_forces_matrix[i][1];

            propelling_vel[i][0] = cos(propelling_angle[i]);
            propelling_vel[i][1] = sin(propelling_angle[i]);

            for (int dim = 0; dim < 2.f; dim ++) {
                if (pos[i][dim] > size/2.f)
                    pos[i][dim] = -size/2.f;
                else if (pos[i][dim] < -size/2.f)
                    pos[i][dim] = size/2.f;
            }

            // Debug
            sum_forces_matrix_debug[i][0] = sum_forces_matrix[i][0];
            sum_forces_matrix_debug[i][1] = sum_forces_matrix[i][1];
            //

            sum_forces_matrix[i][0] = 0.f;
            sum_forces_matrix[i][1] = 0.f;
        }
    }

    void update_normal() {
        // Debug
        rng_manager.update();
        pairs_computed = vector<array<int, 2>>();
        
        superposition_count = 0;
        //  
        
        for (int i=0; i < n-1; i++) {
            // array<double, 2> &pos_i = pos[i];
            for (int j=i+1; j < n; j++) {
                // array<double, 2> &other = pos[j]; 
                calc_force(i, j);
                
                // double dx = other[0] - pos_i[0];
                // double dy = other[1] - pos_i[1];
                // double dist = sqrt(dx*dx + dy*dy);

                // if (dist > max_r) {
                //     continue;
                // }

                // if (dist < 1e-6) {
                //     sum_forces_matrix[i][0] += propelling_cfg.max_repulsive_force;
                //     sum_forces_matrix[i][1] += 0;

                //     sum_forces_matrix[j][0] += -propelling_cfg.max_repulsive_force;
                //     sum_forces_matrix[j][1] += 0;
                //     continue;
                // }

                // double scalar;
                // if (dist < r_eq) {
                //     scalar = max_repulsive_force * (dist - r_eq) / r_eq;
                // } else {
                //     scalar = max_attractive_force * (dist - r_eq) / (max_r - r_eq);
                // }

                // sum_forces_matrix[i][0] += dx/dist * scalar;
                // sum_forces_matrix[i][1] += dy/dist * scalar;

                // sum_forces_matrix[j][0] += -dx/dist * scalar;
                // sum_forces_matrix[j][1] += -dy/dist * scalar;
            }
        }

        for (int i=0; i < n; i++) {
            pos[i][0] += dt * vel[i][0];
            pos[i][1] += dt * vel[i][1];
            
            // random_number = (double)rand();
            // Debug
            random_number = (double)rng_manager.get_random_num(i);
            //

            double noise = 1. / (2. * sqrt(dt)) * (2. * random_number/(double)RAND_MAX - 1.);
            double random_angle = noise * nabla;
            double speed = sqrt(vel[i][0]*vel[i][0] + vel[i][1]*vel[i][1]);
            double cross_prod = propelling_vel[i][0] * vel[i][1]/speed - propelling_vel[i][1] * vel[i][0]/speed;
            double angle_derivate = 1.f / relaxation_time * asin(cross_prod) + random_angle;  

            propelling_angle[i] += angle_derivate * dt;

            // cout << propelling_angle[0] << endl;
            // cout << sum_forces_matrix[0][0] << ", " << sum_forces_matrix[0][1] << endl;

            vel[i][0] = vo * propelling_vel[i][0] + mobility * sum_forces_matrix[i][0];
            vel[i][1] = vo * propelling_vel[i][1] + mobility * sum_forces_matrix[i][1];

            propelling_vel[i][0] = cos(propelling_angle[i]);
            propelling_vel[i][1] = sin(propelling_angle[i]);

            for (int dim = 0; dim < 2.f; dim ++) {
                if (pos[i][dim] > size/2.f)
                    pos[i][dim] = -size/2.f;
                else if (pos[i][dim] < -size/2.f)
                    pos[i][dim] = size/2.f;
            }

            // Debug
            sum_forces_matrix_debug[i][0] = sum_forces_matrix[i][0];
            sum_forces_matrix_debug[i][1] = sum_forces_matrix[i][0];
            //

            sum_forces_matrix[i][0] = 0.f;
            sum_forces_matrix[i][1] = 0.f;
        }
    }

    double mean_vel() {
        double sum_vel[2] = {0, 0};
        for (array<double, 2> vel_i: vel) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        double speed_total = sqrt(sum_vel[0]*sum_vel[0] + sum_vel[1]*sum_vel[1]);
        return speed_total / n;
    }

    array<double, 2> mean_vel_vec() {
        array<double, 2> sum_vel = {0., 0.};
        for (array<double, 2> vel_i: vel) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        sum_vel[0] /= (double)n;
        sum_vel[1] /= (double)n;
        return sum_vel;
    }
};

class Vicsek {
private:
    double nabla;
    double alpha;
    double ro;
    double vo;
    vector<double> new_angles;
    vector<array<double, 2>> sum_vel_matrix;
    
    double size;
    double dt;
    
    int n;
public:
    vector<array<double, 2>> pos;
    vector<array<double, 2>> vel;
    
    Vicsek(vector<array<double, 2>> pos0, vector<array<double, 2>> vel0, double alpha, double nabla,
        double ro, double vo, double size, double dt) 
    : nabla(nabla), alpha(alpha), ro(ro), vo(vo), size(size), dt(dt), pos(pos0), vel(vel0)
    {
        sum_vel_matrix = vector<array<double, 2>>(n, {0., 0.});
        new_angles = vector<double>(n, 0.);
    }

    void update_third_law() {
        for (int i=0; i < n; i++) {
            array<double, 2> &pos_i = pos[i];

            for (int j=i; j < n; j++) {
                array<double, 2> &other = pos[j]; 
             
                double dx = pos_i[0] - other[0];
                double dy = pos_i[1] - other[1];
                double dist = sqrt(dx*dx + dy*dy);

                if (dist < ro) {
                    sum_vel_matrix[i][0] += vel[j][0];
                    sum_vel_matrix[i][1] += vel[j][1];
                    
                    if (j != i) {
                        sum_vel_matrix[j][0] += vel[i][0];
                        sum_vel_matrix[j][1] += vel[i][1];
                    }
                }
            }
        }

        for (int i=0; i < n; i++) {
            double random_angle = (2. * (double)rand()/(double)RAND_MAX - 1.) * nabla / 2.0;
            double angle = alpha * atan2(sum_vel_matrix[i][1], sum_vel_matrix[i][0]) + random_angle;  

            vel[i][0] = cos(angle) * vo;
            vel[i][1] = sin(angle) * vo;

            pos[i][0] += dt * vel[i][0];
            pos[i][1] += dt * vel[i][1];

            for (int dim = 0; dim < 2; dim ++) {
                if (pos[i][dim] > size/2)
                    pos[i][dim] = -size/2;
                else if (pos[i][dim] < -size/2)
                    pos[i][dim] = size/2;
            }

            sum_vel_matrix[i][0] = 0;
            sum_vel_matrix[i][1] = 0;
        }
    }

    void update_basic() {
        for (int i=0; i < n; i++) {
            array<double, 2> &pos_i = pos[i];
            double sum_vel[2] = {0, 0};

            for (int j=0; j < n; j++) {
                array<double, 2> &other = pos[j]; 
             
                double dx = pos_i[0] - other[0];
                double dy = pos_i[1] - other[1];
                double dist = sqrt(dx*dx + dy*dy);

                if (dist < ro) {
                    sum_vel[0] += vel[j][0];
                    sum_vel[1] += vel[j][1];
                }
            }
    
            if (sum_vel[0] == 0.0) {
                sum_vel[0] = 1e-6;
            }

            double random_angle = (2. * (double)rand()/(double)RAND_MAX - 1.) * nabla / 2.0;
            // cout << random_angle << endl;

            new_angles[i] = alpha * atan2(sum_vel[1], sum_vel[0]) + random_angle;
        }

        for (int i = 0; i < n; i ++) {
            double angle = new_angles[i];
            vel[i][0] = cos(angle);
            vel[i][1] = sin(angle);

            pos[i][0] += dt * vel[i][0];
            pos[i][1] += dt * vel[i][1];

            for (int dim = 0; dim < 2; dim ++) {
                if (pos[i][dim] > size/2)
                    pos[i][dim] = -size/2;
                else if (pos[i][dim] < -size/2)
                    pos[i][dim] = size/2;
            }
        }
    }
};