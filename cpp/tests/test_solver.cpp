#include <iostream>
#include <vector>
#include <array>
#include <cstdlib> 

#include "../src/solver.h"
#include "../src/windows_manager.h"

using namespace std;

void generate_initial_state(vector<array<double, 2>> &pos, vector<array<double, 2>> &vel, double vo,
    int size, int n) {
    for (int i = 0; i < n; i++) {
        array<double, 2> pi = {size/2. * (double)rand()/RAND_MAX, size/2. * (double)rand()/RAND_MAX};

        double angle_i = (double)rand()/RAND_MAX * M_PI * 2;
        array<double, 2> vi = {vo * cos(angle_i), vo * sin(angle_i)};

        pos.push_back(pi);
        vel.push_back(vi);
    }
}

void generate_raw_arrays(double** &pos, double** &vel, double vo, int size, int n) {
    double* pos_row_data = new double[2*n];
    pos = new double*[n];
    
    double* vel_row_data = new double[2*n];
    vel = new double*[n];

    for (int i=0; i < n; i++) {
        pos[i] = pos_row_data + i * 2;
        vel[i] = vel_row_data + i * 2;

        // cout << 10. * (2. * (double)rand()/(double)RAND_MAX - 1.) << endl;
        pos[i][0] = size * (2. * (double)rand()/(double)RAND_MAX - 1.);
        pos[i][1] = size * (2. * (double)rand()/(double)RAND_MAX - 1.);
        
        vel[i][0] = vo * (2. * (double)rand()/(double)RAND_MAX - 1.);
        vel[i][1] = vo * (2. * (double)rand()/(double)RAND_MAX - 1.);
    }
}

int get_window_id(const array<int, 2> &id, int num_cols) {
        return (id[0]%num_cols) * num_cols + (id[1] % num_cols);
}

void test_windows_neighbors(vector<array<double, 2>> &pos) {
    const int num_cols = 4;

    array<array<int, 8>, num_cols*num_cols> check;
    for (int i=0; i<num_cols; i ++) {
        for (int j=0; j<num_cols; j ++) {
            auto win_2d_id = array<int, 2>({i, j});
            int win_id = get_window_id(win_2d_id, num_cols);

            int col_id = win_2d_id[1]-1;
            if (col_id == -1) {
                col_id = num_cols - 1;
            }
            check[win_id][0] = get_window_id({win_2d_id[0] + 1, col_id}, num_cols);
            
            check[win_id][1] = get_window_id({win_2d_id[0] + 1, win_2d_id[1]}, num_cols);
            check[win_id][2] = get_window_id({win_2d_id[0] + 1, win_2d_id[1]+1}, num_cols);
            
            int row_id = win_2d_id[0] - 1;
            if (row_id == -1) {
                row_id = num_cols - 1;
            }
            
            col_id = win_2d_id[1]-1;
            if (col_id == -1) {
                col_id = num_cols - 1;
            }
            check[win_id][3] = get_window_id({row_id, col_id}, num_cols);
            check[win_id][4] = get_window_id({row_id, win_2d_id[1]}, num_cols);
            check[win_id][5] = get_window_id({row_id, win_2d_id[1]+1}, num_cols);

            col_id = win_2d_id[1]-1;
            if (col_id == -1) {
                col_id = num_cols - 1;
            }
            check[win_id][6] = get_window_id({win_2d_id[0], col_id}, num_cols);
            check[win_id][7] = get_window_id({win_2d_id[0], win_2d_id[1]+1}, num_cols);
        }
    }

    array<vector<int>, num_cols*num_cols> check2;
    // for (int i =0; i < num_cols*num_cols; i ++) {
        
    //     for (int j=0; j < 8; j++) {
    //         check2[i][j] = 0;
    //     }
    // }

    WindowsManager window_manager = WindowsManager(&pos, num_cols, num_cols, 20.0);
    for (auto win_id: window_manager.windows_ids) {
        cout << "##" <<  win_id[0] << ", " << win_id[1] << "##" << endl;
        int win_scalar_id = get_window_id(win_id, num_cols);
        for (auto neighbor_id: window_manager.window_neighbor[win_id[0]][win_id[1]]) {
            cout << neighbor_id[0] << ", " << neighbor_id[1] << endl;

            int win_neigh_scalar_id = get_window_id(neighbor_id, num_cols);
            check2[win_scalar_id].push_back(win_neigh_scalar_id);
            check2[win_neigh_scalar_id].push_back(win_scalar_id);
        }
        cout << "====================" << endl;
    }

    for (int i=0; i<num_cols*num_cols; i++) {
        cout << i << "("  << check2[i].size() << ")" << ": ";
        for (int j=0; j<check2[i].size(); j++) {
            int curr_neigh = check2[i][j];

            int window_count = 0;
            for (int k=0; k<8; k++) {
                if (check2[i][k] == curr_neigh)
                    window_count ++;
            }
            if (window_count != 1)
                cout << "Duplicado!";

            bool has_error = true;
            for (int k=0; k<8; k++) {
                if (check[i][k] == curr_neigh) {
                    has_error = false;
                    break;
                }
            }

            if (has_error == true) {
                cout << "Erro!";
                // break;
            }

            cout << check2[i][j] << ", ";
        }
        cout << endl << "      ";

        for (int j=0; j<check[i].size(); j++) {
            cout << check[i][j] << ", ";
        }


        cout << endl << endl;
    }
}

int main() {
    int n = 20;
    double size = 10;
    double dt = 0.05;
    
    SelfPropellingCfg self_prop_cfg;
    self_prop_cfg.max_attractive_force = 1; 
    self_prop_cfg.max_repulsive_force = 1; 
    self_prop_cfg.max_r = 1; 
    self_prop_cfg.r_eq = 5./6.; 
    self_prop_cfg.mobility = 1;
    self_prop_cfg.relaxation_time = 1;
    self_prop_cfg.vo = 1;
    self_prop_cfg.nabla = 11; 

    // double** pos;
    // double** vel;
    // generate_raw_arrays(pos, vel, vo, size, n);
    // for (int i=0; i < n; i++) {
        // cout << pos[i][0] << ", " << pos[i][1] <<  endl;
    // }

    vector<array<double, 2>> p;
    vector<array<double, 2>> v;
    generate_initial_state(p, v, self_prop_cfg.vo, size, n);

    // test_windows_neighbors(p);

    // SelfPropelling s = SelfPropelling(p, v, self_prop_cfg, size, dt);
    SelfPropelling s = SelfPropelling(p, v, self_prop_cfg, size, dt, 10);
    
    for (int i=0; i < 4; i++) {
        s.update_windows();
        // s.update_normal();
        cout << s.propelling_angle[2] << endl;
        cout << s.pos[0][0] << ", " << s.pos[0][1] << endl;
    }
}