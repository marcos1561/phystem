#pragma once

#include <vector>
#include <array>

#include "windows_manager.h"

using Vector3d = std::vector<std::vector<std::array<double, 2>>>;
using Vector2d = std::vector<std::array<double, 2>>;

class InPolChecker {
public:
    Vector3d* pols;
    Vector2d* center_mass;
    double space_size;
    int update_freq;
    bool disable;

    Vector2d inside_points;
    int num_inside_points;

    WindowsManager windows_manager;

    int num_verts;
    int counter;


    InPolChecker() {};

    InPolChecker(Vector3d *pols, Vector2d *center_mass, double space_size, int num_col_windows, int update_freq=1,
        bool disable=false)
    : pols(pols), center_mass(center_mass), space_size(space_size), update_freq(update_freq), disable(disable) {
        windows_manager = WindowsManager(center_mass, num_col_windows, num_col_windows, space_size);
        std::cout << "update_freq: " << update_freq << std::endl; 
        num_verts = (*pols)[0].size();
        num_inside_points = 0;
        counter = 1;
    }

    bool is_inside_pol(double x, double y, int pol_id) {
        bool is_inside = false;
        bool test1, test2;

        auto& pol_i = (*pols)[pol_id];

        for (int i = 0; i < num_verts-1; i++)
        {
            auto &vert1 = pol_i[i];
            auto &vert2 = pol_i[i+1];
        
            test1 = (vert2[1] > y) != (vert1[1] > y);
            test2 = x < (vert1[0] - vert2[0]) * (y-vert2[1]) / (vert1[1]-vert2[1]) + vert2[0];
            if (test1 && test2)
                is_inside = !is_inside;
        }
        
        auto &vert1 = pol_i[num_verts-1];
        auto &vert2 = pol_i[0];
    
        test1 = (vert2[1] > y) != (vert1[1] > y);
        test2 = x < (vert1[0] - vert2[0]) * (y-vert2[1]) / (vert1[1]-vert2[1]) + vert2[0];
        if (test1 && test2)
            is_inside = !is_inside;

        return is_inside;
    }

    void check_intersection(int pol_id, int other_id) {
        for (auto &p: (*pols)[pol_id]) {
            if (is_inside_pol(p[0], p[1], other_id) == true) {
                if ((int)inside_points.size() > num_inside_points) {
                    inside_points[num_inside_points] = p;
                } else {
                    inside_points.push_back(p);
                }

                num_inside_points += 1;
                break;
            }
        }
    }

    void update() {
        if (disable) 
            return;

        if (counter % (update_freq) == 0) {
            counter = 1;
        } else {
            counter ++;
            return;
        }

        windows_manager.update_window_members();
        num_inside_points = 0;

        for (auto win_id: windows_manager.windows_ids) {
            auto & window = windows_manager.windows[win_id[0]][win_id[1]];
            auto & neighbors = windows_manager.window_neighbor[win_id[0]][win_id[1]];
            int windows_cap = windows_manager.capacity[win_id[0]][win_id[1]];
            
            for (int i=0; i < windows_cap; i++) {
                auto pol_id = window[i];

                for (int j = i+1; j < windows_cap; j ++) {
                    auto other_id = window[j];
                    check_intersection(pol_id, other_id);
                    check_intersection(other_id, pol_id);
                }

                for (auto neigh_id : neighbors) {
                    auto & neigh_window = windows_manager.windows[neigh_id[0]][neigh_id[1]];
                    int neigh_window_cap = windows_manager.capacity[neigh_id[0]][neigh_id[1]];

                    for (int j = 0; j < neigh_window_cap; j ++) {
                        auto other_id = neigh_window[j];
                        check_intersection(pol_id, other_id);
                        check_intersection(other_id, pol_id);
                    }
                }
            } 
        }
    }

};

// void in_pol_checker(Vector3d &pols) {

// }
