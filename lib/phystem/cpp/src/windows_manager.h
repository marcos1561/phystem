/**
 * TODO: O sistema apenas funciona se o número de colunas (n) é maior ou igual a 3.
 *      Problema: Geração dos vizinhos, pois nos caso n < 3, ocorre intersecção de vizinhos.
*/

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

    vector<array<double, 2>> *point_pos;
    int num_cols;
    int num_rows;
    int num_points;
    double space_size;
    int update_freq;

    int counter;

public:
    WindowsManager() {};

    WindowsManager(vector<array<double, 2>> *p_pos, int num_cols, int num_rows, double space_size) : 
    point_pos(p_pos), num_cols(num_cols), num_rows(num_rows), space_size(space_size) {
        num_points = point_pos->size();
        col_size = space_size/(double)num_cols;
        row_size = space_size/(double)num_rows;

        counter = 0;

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

class WindowsManagerRing {
public:
    double col_size;
    double row_size;
    vector<vector<vector<array<int, 2>>>> windows;
    vector<vector<int>> capacity;

    vector<array<int, 2>> windows_ids;
    vector<vector<vector<array<int, 2>>>> window_neighbor;

    vector<vector<array<double, 2>>> *point_pos;
    int num_cols;
    int num_rows;
    int num_entitys;
    int num_points;
    double space_size;
    int update_freq;

    int counter;

public:
    WindowsManagerRing() {};

    WindowsManagerRing(vector<vector<array<double, 2>>> *p_pos, int num_cols, int num_rows, double space_size,
        int update_freq=1) : point_pos(p_pos), num_cols(num_cols), num_rows(num_rows), space_size(space_size),
        update_freq(update_freq) {
        num_entitys = point_pos->size();
        num_points = (*point_pos)[0].size();
        col_size = space_size/(double)num_cols;
        row_size = space_size/(double)num_rows;

        counter = 0;

        int average_num_points = num_points/(num_cols*num_rows);
        auto row = vector<vector<array<int, 2>>>(num_cols, vector<array<int, 2>>(average_num_points));
        windows = vector<vector<vector<array<int, 2>>>>(num_rows, row);

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
        
        // window_neighbor = vector<vector<vector<array<int, 2>>>>(num_rows, vector<vector<array<int, 2>>>(num_cols));
        // for (int i = 0; i < num_rows; i++) {
        //     auto possible_neighbors = vector<array<int, 2>>();
        //     for (int j = 0; j < num_cols; j++) {
        //         possible_neighbors.push_back({i, (j+1)%num_cols});
        //         possible_neighbors.push_back({(i+1)%num_rows, j});
        //         possible_neighbors.push_back({(i+1)%num_rows, (j+1)%num_cols});

        //         if ((j-1) == -1) {
        //             possible_neighbors.push_back({(i+1)%num_rows, num_cols-1});
        //         }
        //         else {
        //             possible_neighbors.push_back({(i+1)%num_rows, (j-1)});
        //         }

        //         for (auto neighbor: possible_neighbors) {
        //             if ((neighbor[0] == i) & (neighbor[1] == j)) {
        //                 continue;
        //             }
        //             window_neighbor[i][j].push_back(neighbor);
        //         }
        //     }
        // }
    }

    void update_window_members() {
        if ((counter % update_freq) != 0) {
            counter ++;
            return;
        } else {
            counter = 1;
        }

        for (int i = 0; i < num_rows; i ++) {
            for (int j = 0; j < num_cols; j ++) {
                capacity[i][j] = 0;
            }
        }

        for (int entity_id = 0; entity_id < num_entitys; entity_id++)
        {
            for (int p_id=0; p_id < num_points; p_id ++) 
            {
                int col_pos = (int)(((*point_pos)[entity_id][p_id][0] + space_size/2.) / col_size);
                int row_pos = (int)(((*point_pos)[entity_id][p_id][1] + space_size/2.) / row_size);

                if (row_pos == num_rows)
                    row_pos -= 1;
                if (col_pos == num_cols)
                    col_pos -= 1;

                size_t id = capacity[row_pos][col_pos];
                
                if (id < windows[row_pos][col_pos].size()) {
                    windows[row_pos][col_pos][id] = {entity_id, p_id};
                } else {
                    windows[row_pos][col_pos].push_back({entity_id, p_id});
                }
                
                capacity[row_pos][col_pos] += 1;
            }
        }
    }
};
