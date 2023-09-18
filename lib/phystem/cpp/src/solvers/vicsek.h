#include <cmath>
#include <vector>
#include <array>
#include <iostream>
#include <cstdlib> 

#include "../configs.h"
#include "../rng_manager.h"
#include "../windows_manager.h"

using namespace std;

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