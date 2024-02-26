#include <array>
#include <iostream>

#include "../../src/in_pol_checker.h"

int main() {
    Vector3d pols = {
        {{0, 0}, {1, 0}, {1, 1}, {0, 1}},
        {{0.5, 0.5}, {1.5, 0.5}, {1.5, 1.5}, {0.5, 1.5}},
    };

    Vector2d cms;
    for (auto& p: pols) {
        std::array<double, 2> cm = {0, 0};
        for (auto& v: p) {
            cm[0] += v[0];
            cm[1] += v[1];
        }
        cm[0] /= p.size();
        cm[1] /= p.size();
        cms.push_back(cm);            
    }

    InPolChecker pol_checker(&pols, &cms, 3, 10);

    pol_checker.update();

    std::cout << pol_checker.num_inside_points << std::endl;
    
    for (auto& in_p: pol_checker.inside_points) {
        std::cout << in_p[0] << ", " << in_p[1] << std::endl;
    }
}