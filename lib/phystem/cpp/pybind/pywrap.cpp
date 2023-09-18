#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

#include "../src/solvers/self_propelling.h"
#include "../src/solvers/ring.h"
#include "../src/configs/python_configs.h"

using namespace std;

PYBIND11_MAKE_OPAQUE(vector<array<double, 2>>);
PYBIND11_MAKE_OPAQUE(vector<vector<double*>>);
PYBIND11_MAKE_OPAQUE(vector<double>);

using List = vector<double>;
using VecList = vector<array<double, 2>>;
using PyVecList = vector<vector<double*>>;

namespace py = pybind11;
constexpr auto byref = py::return_value_policy::reference_internal;

PYBIND11_MODULE(cpp_lib, m) {
    auto data_types = m.def_submodule("data_types");
    auto solvers = m.def_submodule("solvers");
    auto configs = m.def_submodule("configs");
    auto managers = m.def_submodule("managers");

    //==
    // Data Types
    //==
    py::bind_vector<PyVecList>(data_types, "PyVecList");
    py::bind_vector<VecList>(data_types, "PosVec");
    py::bind_vector<List>(data_types, "List");

    //==
    // Configs
    //==
    py::class_<SelfPropellingCfgPy>(configs, "SelfPropellingCfg")
        .def(py::init<py::dict &>())
        .def("info", &SelfPropellingCfgPy::info)
        ;
 
    py::class_<RingCfgPy>(configs, "RingCfg")
        .def(py::init<py::dict &>())
        ;

    //==
    // Manager
    //==
    py::class_<RngManager>(managers, "RngManager")
        .def(py::init<int>())
        .def_readonly("random_nums", &RngManager::random_nums, byref)
        ;

    py::class_<WindowsManager>(managers, "WindowsManager")
        .def(py::init<VecList*, int, int, double>())
        .def("update_window_members", &WindowsManager::update_window_members)
        .def_readonly("col_size", &WindowsManager::col_size)
        .def_readonly("row_size", &WindowsManager::row_size)
        .def_readonly("windows", &WindowsManager::windows)
        .def_readonly("capacity", &WindowsManager::capacity)
        .def_readonly("windows_ids", &WindowsManager::windows_ids)
        .def_readonly("window_neighbor", &WindowsManager::window_neighbor)
        ;

    //==
    // Solvers
    //==
    py::class_<SelfPropelling>(solvers, "SelfPropelling")
        .def(py::init<vector<array<double, 2>>&, vector<array<double, 2>>&, SelfPropellingCfgPy, 
            double, double, int, double>(), py::arg("pos0"), py::arg("vel0"), py::arg("propelling_cfg"), 
            py::arg("size"), py::arg("dt"), py::arg("num_windows"), py::arg("seed")=-1.)
        .def("update_normal", &SelfPropelling::update_normal, py::call_guard<py::gil_scoped_release>())
        .def("update_windows", &SelfPropelling::update_windows, py::call_guard<py::gil_scoped_release>())
        .def("mean_vel", &SelfPropelling::mean_vel)
        .def("mean_vel_vec", &SelfPropelling::mean_vel_vec)
        .def_readonly("pos", &SelfPropelling::pos, byref)
        .def_readonly("vel", &SelfPropelling::vel, byref)
        .def_readonly("propelling_vel", &SelfPropelling::propelling_vel, byref)
        .def_readonly("propelling_angle", &SelfPropelling::propelling_angle, byref)
        .def_readonly("py_pos", &SelfPropelling::py_pos, byref)
        .def_readonly("py_vel", &SelfPropelling::py_vel, byref)
        .def_readonly("py_propelling_vel", &SelfPropelling::py_propelling_vel, byref)
        .def_readonly("rng_manager", &SelfPropelling::rng_manager, byref)
        .def_readonly("random_number", &SelfPropelling::random_number, byref)
        .def_readonly("superposition_count", &SelfPropelling::superposition_count, byref)
        .def_readonly("sum_forces_matrix_debug", &SelfPropelling::sum_forces_matrix_debug, byref)
        .def_readonly("n", &SelfPropelling::n, byref)
        ;
    
    py::class_<Ring>(solvers, "Ring")
        .def(py::init<VecList&, VecList&, vector<double>&, RingCfgPy, 
            double, double, int>(), py::arg("pos0"), py::arg("vel0"), py::arg("self_prop_angle0"), 
            py::arg("dynamic_cfg"), py::arg("size"), py::arg("dt"), py::arg("seed")=-1)
        .def("update_normal", &Ring::update_normal, py::call_guard<py::gil_scoped_release>())
        .def("mean_vel", &Ring::mean_vel)
        .def("mean_vel_vec", &Ring::mean_vel_vec)
        .def_readonly("pos", &Ring::pos, byref)
        .def_readonly("vel", &Ring::vel, byref)
        .def_readonly("self_prop_vel", &Ring::self_prop_vel, byref)
        .def_readonly("self_prop_angle", &Ring::self_prop_angle, byref)
        .def_readonly("pos_t", &Ring::pos_t, byref)
        .def_readonly("graph_points", &Ring::graph_points, byref)
        .def_readonly("count_overlap", &Ring::count_overlap)
        .def_readonly("count_zero_speed", &Ring::count_zero_speed)
        .def_readonly("spring_forces", &Ring::spring_forces)
        .def_readonly("total_forces", &Ring::total_forces)
        .def_readonly("vol_forces", &Ring::vol_forces)
        ;
}