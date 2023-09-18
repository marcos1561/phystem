#pragma once

#include <pybind11/pybind11.h>
#include "self_propelling.h"
#include "ring.h"

namespace py = pybind11;
using namespace std;

class SelfPropellingCfgPy: public SelfPropellingCfg {
public:
    SelfPropellingCfgPy(py::dict values) {
        // Constructor for Python
        mobility = py::float_(values["mobility"]);
        relaxation_time = py::float_(values["relaxation_time"]);
        vo = py::float_(values["vo"]);
        nabla = py::float_(values["nabla"]);
        max_attractive_force = py::float_(values["max_attractive_force"]);
        max_repulsive_force = py::float_(values["max_repulsive_force"]);
        r_eq = py::float_(values["r_eq"]);
        max_r = py::float_(values["max_r"]);
    };
};

class RingCfgPy: public RingCfg {
public:
    RingCfgPy(py::dict values) {
        // Constructor for Python
        spring_k = py::float_(values["spring_k"]);
        spring_r = py::float_(values["spring_r"]);
        
        bend_k = py::float_(values["bend_k"]);

        mobility = py::float_(values["mobility"]);
        relax_time = py::float_(values["relax_time"]);
        vo = py::float_(values["vo"]);

        trans_diff = py::float_(values["trans_diff"]);
        rot_diff = py::float_(values["rot_diff"]);

        exclusion_vol = py::float_(values["exclusion_vol"]);
        diameter = py::float_(values["diameter"]);
    };
};