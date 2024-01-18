#include "creator.h"
#include "cmath"

ring::Data ring::init_cfg(int num_rings, int num_p, double r, double vo) {
    ring:Data data = Data();

    data.pos = vector<Vector2d>(2);
    data.vel = vector<Vector2d>(2);
    data.self_prop_angle = vector<vector<double>>(2);
    
    double rings_center[] = {-1.3 * r, 1.3 * r};
    // double rings_self_prop_angle[] = {0, M_PI};
    double rings_self_prop_angle[] = {0, 0};

    for (int ring_id = 0; ring_id < 2; ring_id++)
    {
        double dtheta = 2. * M_PI / (double)num_p;
        for (size_t i = 0; i < num_p; i++) {
            double theta = dtheta * (double)i;
            
            array<double, 2> particle_pos = {cos(theta) * r, sin(theta) * r};
            particle_pos[0] += rings_center[ring_id];
            particle_pos[1] += rings_center[ring_id];
            data.pos[ring_id].push_back(particle_pos);
            

            // double angle = 2 * M_PI * (double)rand()/(double)RAND_MAX; 
            double angle = rings_self_prop_angle[ring_id]; 

            data.self_prop_angle[ring_id].push_back(angle);
            data.vel[ring_id].push_back({vo * cos(angle), vo * sin(angle)});
        }
    }

    return data;     
}