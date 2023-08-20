#pragma once

#include <array>
#include <vector>

using namespace std;

class WindowsManager {
public:
    double col_size;
    double row_size;
    vector<vector<vector<int>>> windows;
    vector<vector<int>> capacity;

    vector<array<int, 2>> windows_ids;
    vector<vector<vector<array<int, 2>>>> window_neighbor;

private:
    vector<array<double, 2>> *point_pos;
    int num_cols;
    int num_rows;
    int num_points;
    double space_size;

public:
    WindowsManager() {};

    WindowsManager(vector<array<double, 2>> *p_pos, int num_cols, int num_rows, double space_size) : 
    point_pos(p_pos), num_cols(num_cols), num_rows(num_rows), space_size(space_size) {
        num_points = point_pos->size();
        col_size = space_size/(double)num_cols;
        row_size = space_size/(double)num_rows;

        int average_num_points = num_points/(num_cols*num_rows);
        auto row = vector<vector<int>>(num_cols, vector<int>(average_num_points));
        windows = vector<vector<vector<int>>>(num_rows, row);

        capacity = vector<vector<int>>(num_rows, vector<int>(num_cols, 0));

        for (int i = 0; i < num_rows; i++) {
            for (int j = 0; j < num_cols; j++) {
                windows_ids.push_back({i, j});
            }
        }
        
        window_neighbor = vector<vector<vector<array<int, 2>>>>(num_rows, vector<vector<array<int, 2>>>(num_cols));

        for (int i = 0; i < num_rows; i++) {
            for (int j = 0; j < num_cols; j++) {
                window_neighbor[i][j].push_back({i, (j+1)%num_cols});
                window_neighbor[i][j].push_back({(i+1)%num_rows, j});
                window_neighbor[i][j].push_back({(i+1)%num_rows, (j+1)%num_cols});

                if ((j-1) == -1) {
                    window_neighbor[i][j].push_back({(i+1)%num_rows, num_cols-1});
                }
                else {
                    window_neighbor[i][j].push_back({(i+1)%num_rows, (j-1)});
                }
            }
        }
    }

    void update_window_members() {
        for (int i = 0; i < num_rows; i ++) {
            for (int j = 0; j < num_cols; j ++) {
                capacity[i][j] = 0;
            }
        }

        for (int p_id=0; p_id < num_points; p_id ++) {
            int col_pos = (int)(((*point_pos)[p_id][0] + space_size/2.) / col_size);
            int row_pos = (int)(((*point_pos)[p_id][1] + space_size/2.) / row_size);

            if (row_pos == num_rows)
                row_pos -= 1;
            if (col_pos == num_cols)
                col_pos -= 1;

            size_t id = capacity[row_pos][col_pos];
            
            if (id < windows[row_pos][col_pos].size()) {
                windows[row_pos][col_pos][id] = p_id;
            } else {
                windows[row_pos][col_pos].push_back(p_id);
            }
            
            capacity[row_pos][col_pos] += 1;
        }
    }
};
