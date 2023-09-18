#pragma once

#include <vector>
#include <cstdlib> 

using namespace std;

class RngManager {
public:
    int n;
    int n_rng;
    vector<vector<int>> random_nums;

    RngManager() {}

    RngManager(int num_particles, int num_rng_per_particle=1) {
        n = num_particles;
        n_rng = num_rng_per_particle;
        random_nums = vector<vector<int>>(num_particles, vector<int>(n_rng));
    }

    vector<int>& get_random_num(int id) {
        return random_nums[id];
    }

    void update() {
        for (int i=0; i < n; i++) {
            for (int j=0; j < n_rng; j++) {
                random_nums[i][j] = rand();
            }
        }
    }
};