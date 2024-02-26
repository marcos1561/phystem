#pragma once

#include <vector>
#include <cstdlib> 

using namespace std;

class RngManager {
public:
    int num_entities;
    int num_particles;
    int num_rng_per_particle;
    vector<vector<vector<int>>> random_nums;

    RngManager() {}

    RngManager(int num_particles, int num_entities=1, int num_rng_per_particle=1)
        : num_entities(num_entities), num_particles(num_particles), num_rng_per_particle(num_rng_per_particle)
    {
        // random_nums = vector<vector<int>>(num_particles, vector<int>(num_rng_per_particle));
        auto entity_random_nums = vector<vector<int>>(num_particles, vector<int>(num_rng_per_particle));
        random_nums = vector<vector<vector<int>>>(num_entities, entity_random_nums);
    }

    vector<int>& get_random_num(int id, int entity_id=0) {
        return random_nums[entity_id][id];
    }

    void update() {
        for (int entity_id = 0; entity_id < num_entities; entity_id++) {
            for (int i=0; i < num_particles; i++) {
                for (int j=0; j < num_rng_per_particle; j++) {
                    random_nums[entity_id][i][j] = rand();
                }
            }
        }
    }
};