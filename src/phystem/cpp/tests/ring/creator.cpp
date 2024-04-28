#include "creator.h"
#include "cmath"

ring::Data ring::init_cfg(int num_rings, int num_p, double r, double vo) {
    ring:Data data = Data();

    data.pos = vector<Vector2d>(2);
    data.self_prop_angle = vector<double>(num_rings);
    
    double rings_center_x[] = {-1.3 * r, 1.3 * r};

    for (int ring_id = 0; ring_id < 2; ring_id++)
    {
        double dtheta = 2. * M_PI / (double)num_p;
        for (size_t i = 0; i < num_p; i++) {
            double theta = dtheta * (double)i;
            
            array<double, 2> particle_pos = {cos(theta) * r, sin(theta) * r};
            particle_pos[0] += rings_center_x[ring_id];
            data.pos[ring_id].push_back(particle_pos);
        }

        double angle = 2 * M_PI * (double)rand()/(double)RAND_MAX; 
        data.self_prop_angle.push_back(angle);
    }

    return data;     
}