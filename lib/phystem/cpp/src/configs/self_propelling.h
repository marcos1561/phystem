#pragma once

#include <iostream>

using namespace std;

class SelfPropellingCfg {
public:
    double mobility;
    
    double relaxation_time;
    double vo;
    double nabla;

    double max_attractive_force;
    double max_repulsive_force;
    double r_eq;
    double max_r;

    SelfPropellingCfg() {};
    
    SelfPropellingCfg(double mobility, double relaxation_time, double vo, double nabla, 
        double max_attractive_force, double max_repulsive_force, double r_eq, double max_r)
        : mobility(mobility), relaxation_time(relaxation_time), vo(vo), nabla(nabla), 
        max_attractive_force(max_attractive_force), max_repulsive_force(max_repulsive_force),
        r_eq(r_eq), max_r(max_r) {};
    
    void info() {
        cout << "Mobility             : " << mobility << endl;
        cout << "Relaxation_time      : " << relaxation_time << endl;
        cout << "V_o                  : " << vo << endl;
        cout << "Nabla                : " << nabla << endl;
        cout << "Max_attractive_force : " << max_attractive_force << endl;
        cout << "Max_repulsive_force  : " << max_repulsive_force << endl;
        cout << "R_eq                 : " << r_eq << endl;
        cout << "Max_r                : " << max_r << endl;
    } 
};