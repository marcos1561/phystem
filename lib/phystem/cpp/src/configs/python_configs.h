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
        
        k_bend = py::float_(values["k_bend"]);
        p0 = py::float_(values["p0"]);
        area0 = py::float_(values["area0"]);

        mobility = py::float_(values["mobility"]);
        relax_time = py::float_(values["relax_time"]);
        vo = py::float_(values["vo"]);

        trans_diff = py::float_(values["trans_diff"]);
        rot_diff = py::float_(values["rot_diff"]);

        // exclusion_vol = py::float_(values["exclusion_vol"]);
        diameter = py::float_(values["diameter"]);
        max_dist = py::float_(values["max_dist"]);
        rep_force = py::float_(values["rep_force"]);
        adh_force = py::float_(values["adh_force"]);
        
        std::string area_potencial_name = py::str(values["area_potencial"]);

        if (area_potencial_name == "format")
            area_potencial = AreaPotencialType::format;
        else if (area_potencial_name == "target_perimeter")
            area_potencial = AreaPotencialType::target_perimeter;
        else if (area_potencial_name == "target_area")
            area_potencial = AreaPotencialType::target_area;
        else
            throw std::invalid_argument("Nome do potencial de area incorreto.");
    };
};

class StokesCfgPy: public StokesCfg {
public:
    StokesCfgPy(py::dict values) {
        obstacle_r = py::float_(values["obstacle_r"]);
        obstacle_x = py::float_(values["obstacle_x"]);
        obstacle_y = py::float_(values["obstacle_y"]);
        
        create_length = py::float_(values["create_length"]);
        remove_length = py::float_(values["remove_length"]);
        
        flux_force = py::float_(values["flux_force"]);

        num_max_rings = py::int_(values["num_max_rings"]);
    }
};