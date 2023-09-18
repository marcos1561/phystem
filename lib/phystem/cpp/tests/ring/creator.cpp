#include "creator.h"
#include "cmath"

ring::Data ring::init_cfg(int n, double r, double vo) {
    ring:Data data = Data();

    double dtheta = 2. * M_PI / (double)n;
    for (size_t i = 0; i < n; i++) {
        double theta = dtheta * (double)i;
        
        data.pos.push_back({cos(theta) * r, sin(theta) * r});
        
        // double angle = 2 * M_PI * (double)rand()/(double)RAND_MAX; 
        double angle = 0.; 

        data.self_prop_angle.push_back(angle);
        data.vel.push_back({vo * cos(angle), vo * sin(angle)});
    }
    return data;     
}