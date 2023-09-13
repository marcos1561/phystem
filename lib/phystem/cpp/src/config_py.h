#pragma once

#include <pybind11/pybind11.h>
#include "config.h"

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