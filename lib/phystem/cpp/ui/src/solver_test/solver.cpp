#include <cstdlib>

#include "headers/solver.h"

double get_random() {
    return (double)rand() / (double)RAND_MAX * 2 - 1;
}

Solver::Solver(int n, double delta_time) {
    pos = VecList(n);
    for (size_t i = 0; i < pos.size(); i++)
    {
        pos[i] = {get_random(), get_random()};
    }

    dt = delta_time;
    time = 0.0;
}

void Solver::update() {
    float vx = 1.0;
    float vy = 1.0;

    for (size_t i = 0; i < pos.size(); i++)
    {
        pos[i][0] += vx * dt;
        pos[i][1] += vy * dt;
        
        float size = 2.0;
        for (int dim = 0; dim < 2.f; dim ++) {
            if (pos[i][dim] > size/2.f)
                pos[i][dim] -= size;
            else if (pos[i][dim] < -size/2.f)
                pos[i][dim] += size;
        }
    }
    
    time += dt;
}