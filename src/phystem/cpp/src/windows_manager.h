/**
 * TODO: O sistema apenas funciona se o número de colunas (n) é maior ou igual a 3.
 *      Problema: Geração dos vizinhos, pois nos caso n < 3, ocorre intersecção de vizinhos.
*/

#pragma once

#include <array>
#include <vector>

using namespace std;

struct SpaceInfo {
    double height;
    double length;
    std::array<double, 2> center;
    
    SpaceInfo() { };

    SpaceInfo(double size, std::array<double, 2> center={{0.0, 0.0}}) :
        height(size), length(size), center(center) { }
    
    SpaceInfo(double height, double length, std::array<double, 2> center={{0.0, 0.0}}) :
        height(height), length(length), center(center) { }
};

class WindowsManager {
public:
    double col_size;
    double row_size;
    vector<vector<vector<int>>> windows;
    vector<vector<int>> capacity;

    vector<array<int, 2>> windows_ids;
    vector<vector<array<double, 2>>> windows_center;
    vector<vector<vector<array<int, 2>>>> window_neighbor;

    double window_length;
    double window_height;

    vector<array<double, 2>> *point_pos;
    vector<int> *ids;
    int *num_active;
    int num_cols;
    int num_rows;
    int num_points;

    SpaceInfo space_info;

    int update_freq;
    int counter;

public:
    WindowsManager() {};

    WindowsManager(vector<array<double, 2>> *p_pos, vector<int> *ids , int *num_active, int num_cols, int num_rows, SpaceInfo space_info) : 
    point_pos(p_pos), ids(ids), num_active(num_active), num_cols(num_cols), num_rows(num_rows), space_info(space_info) {
        num_points = point_pos->size();
        col_size = space_info.length/(double)num_cols;
        row_size = space_info.height/(double)num_rows;

        counter = 0;

        int average_num_points = num_points/(num_cols*num_rows);
        auto row = vector<vector<int>>(num_cols, vector<int>(average_num_points));
        windows = vector<vector<vector<int>>>(num_rows, row);
        capacity = vector<vector<int>>(num_rows, vector<int>(num_cols, 0));
        
        auto row_center = vector<array<double, 2>>(num_cols);
        windows_center = vector<vector<array<double, 2>>>(num_rows, row_center);

        window_height = space_info.height/(double)num_rows; 
        window_length = space_info.length/(double)num_cols; 

        double center_x, center_y;
        for (int i = 0; i < num_rows; i++) {
            center_y = space_info.height/2. + window_height * (0.5 - (double)(i + 1));
            center_y += space_info.center[1];
            
            for (int j = 0; j < num_cols; j++) {
                windows_ids.push_back({i, j});
            
                center_x = -space_info.length/2. + window_length * (-0.5 + (double)(j + 1));
                center_x += space_info.center[0];
                windows_center[i][j] = {center_x, center_y};
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

    void update_point(int p_id) {
        int col_pos = (int)(((*point_pos)[p_id][0] - space_info.center[0] + space_info.length/2.) / col_size);
        int row_pos = (int)(((*point_pos)[p_id][1] - space_info.center[1] + space_info.height/2.) / row_size);

        if (row_pos == num_rows)
            row_pos -= 1;
        if (col_pos == num_cols)
            col_pos -= 1;

        // if ((row_pos >= num_rows) | (row_pos < 0)) {
        //     std::cout << "(Normal) row_pos out_of_bounds | " << row_pos  << std::endl;
        // }
        // if ((col_pos >= num_cols) | (col_pos < 0)) {
        //     std::cout << "(Normal) col_pos out_of_bounds | " << col_pos  << std::endl;
        // }

        size_t id = capacity[row_pos][col_pos];
        
        if (id < windows[row_pos][col_pos].size()) {
            windows[row_pos][col_pos][id] = p_id;
        } else {
            windows[row_pos][col_pos].push_back(p_id);
        }
        
        capacity[row_pos][col_pos] += 1;
    }

    void update_window_members() {
        for (int i = 0; i < num_rows; i ++) {
            for (int j = 0; j < num_cols; j ++) {
                capacity[i][j] = 0;
            }
        }

        // for (int p_id=0; p_id < num_points; p_id ++) {
        for (int i = 0; i < *num_active; i++)
        {
            int p_id = (*ids)[i];
            update_point(p_id);
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
    vector<vector<array<double, 2>>> windows_center;
    vector<vector<vector<array<int, 2>>>> window_neighbor;

    double window_length;
    double window_height;

    vector<vector<array<double, 2>>> *point_pos;
    vector<int> *ids;
    int *num_active;
    int num_cols;
    int num_rows;
    int num_entitys;
    int num_points;
    SpaceInfo space_info;
    double space_size;
    int update_freq;

    int counter;

public:
    WindowsManagerRing() {};

    WindowsManagerRing(vector<vector<array<double, 2>>> *p_pos, vector<int> *ids, int *num_active, int num_cols, 
        int num_rows, SpaceInfo space_info, int update_freq=1) 
        : point_pos(p_pos), ids(ids), num_active(num_active), num_cols(num_cols), num_rows(num_rows), 
        space_info(space_info), update_freq(update_freq) {
        num_entitys = point_pos->size();
        num_points = (*point_pos)[0].size();
        

        col_size = space_info.length/(double)num_cols;
        row_size = space_info.height/(double)num_rows;
        
        // std::cout << "=================" << std::endl;
        // std::cout << "col_size: " << col_size << std::endl;
        // std::cout << "row_size: " << row_size << std::endl;
        // std::cout << "space_length: " << space_info.length << std::endl;
        // std::cout << "space_height: " << space_info.height << std::endl;
        // std::cout << "num_cols: " << num_cols << std::endl;
        // std::cout << "num_rows: " << num_rows << std::endl;

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

        auto row_center = vector<array<double, 2>>(num_cols);
        windows_center = vector<vector<array<double, 2>>>(num_rows, row_center);

        window_height = space_info.height/(double)num_rows; 
        window_length = space_info.length/(double)num_cols; 

        double center_x, center_y;
        for (int i = 0; i < num_rows; i++) {
            center_y = window_height*0.5 + (double)i * window_height - space_info.height*0.5;
            // center_y = space_info.height/2. + window_height * (0.5 - (double)(i + 1));

            center_y += space_info.center[1];
            
            for (int j = 0; j < num_cols; j++) {
                center_x = -space_info.length/2. + window_length * (-0.5 + (double)(j + 1));
                center_x += space_info.center[0];
                windows_center[i][j] = {center_x, center_y};
            }
        }
    }

    std::vector<std::array<int, 2>> get_window_point_elements(float x, float y) {
        /**
         * Retorna os elementos da janela que possui o ponto (x, y).
         */
        int col_pos = (int)((x - space_info.center[0] + space_info.length/2.) / col_size);
        int row_pos = (int)((y - space_info.center[1] + space_info.height/2.) / row_size);

        if (row_pos == num_rows)
            row_pos -= 1;
        if (col_pos == num_cols)
            col_pos -= 1;

        auto window = windows[row_pos][col_pos];
        std::vector<std::array<int, 2>> elements; 
        for (int i = 0; i < capacity[row_pos][col_pos]; i++) {
            elements.push_back(window[i]);
        }

        auto & neighbors = window_neighbor[row_pos][col_pos];
        for (auto neigh_id : neighbors) {
            auto & neigh_window = windows[neigh_id[0]][neigh_id[1]];
            int neigh_window_cap = capacity[neigh_id[0]][neigh_id[1]];

            for (int j = 0; j < neigh_window_cap; j ++) {
                elements.push_back(neigh_window[j]);
            }
        }
        
        return elements;
    }

    std::vector<std::array<int, 2>> get_window_elements(int row_id, int col_id) {
        int cap = capacity[row_id][col_id];
        
        std::vector<std::array<int, 2>> elements; 
        for (int i = 0; i < cap; i++)
        {
            elements.push_back(windows[row_id][col_id][i]);
        }
        
        return elements;
    }

    void update_entity(int entity_id) {
        for (int p_id=0; p_id < num_points; p_id ++) 
        {
            int col_pos = (int)(((*point_pos)[entity_id][p_id][0] - space_info.center[0] + space_info.length/2.) / col_size);
            int row_pos = (int)(((*point_pos)[entity_id][p_id][1] - space_info.center[1] + space_info.height/2.) / row_size);


            if (row_pos == num_rows)
                row_pos -= 1;
            if (col_pos == num_cols)
                col_pos -= 1;

            // std::cout << "Pos: " << (*point_pos)[entity_id][p_id][0] << ", " << (*point_pos)[entity_id][p_id][1] << std::endl;
            // std::cout << "row_size, col_size: " << row_size << ", " << col_size << std::endl;
            // std::cout << "(row, col): " << row_pos << ", " << col_pos << std::endl;
            // std::cout << "---" << std::endl;

            // if ((row_pos >= num_rows) | (row_pos < 0)) {
            //     std::cout << "(Ring) row_pos out_of_bounds | " << row_pos  << std::endl;
            // }
            // if ((col_pos >= num_cols) | (col_pos < 0)) {
            //     std::cout << "(Ring) col_pos out_of_bounds | " << col_pos  << std::endl;
            // }

            size_t id = capacity[row_pos][col_pos];
            
            if (id < windows[row_pos][col_pos].size()) {
                windows[row_pos][col_pos][id] = {entity_id, p_id};
            } else {
                windows[row_pos][col_pos].push_back({entity_id, p_id});
            }
            
            capacity[row_pos][col_pos] += 1;
        }
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

        // for (int entity_id = 0; entity_id < num_entitys; entity_id++)
        // std::cout << "num_active: " << *num_active << std::endl;
        // std::cout << "entity_id:" << std::endl;
        for (int i = 0; i < *num_active; i++)
        {
            int entity_id = (*ids)[i];
            // std::cout << entity_id << std::endl;
            update_entity(entity_id);
        }
    }
};
