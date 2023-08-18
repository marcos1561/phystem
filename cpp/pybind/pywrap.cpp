#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

#include "../src/solver.h"
#include "../src/config_py.h"

using namespace std;

PYBIND11_MAKE_OPAQUE(vector<array<double, 2>>);
PYBIND11_MAKE_OPAQUE(vector<vector<double*>>);

using VecList = vector<array<double, 2>>;
using PyVecList = vector<vector<double*>>;

namespace py = pybind11;
constexpr auto byref = py::return_value_policy::reference_internal;

PYBIND11_MODULE(cpp_lib, m) {
    py::bind_vector<PyVecList>(m, "PyVecList");
    py::bind_vector<VecList>(m, "PosVec");

    py::class_<SelfPropellingCfgPy>(m, "SelfPropellingCfg")
        .def(py::init<py::dict &>())
        .def("info", &SelfPropellingCfgPy::info)
        ;

    py::class_<RngManager>(m, "RngManager")
        .def(py::init<int>())
        .def_readonly("random_nums", &RngManager::random_nums, byref)
        ;

    py::class_<WindowsManager>(m, "WindowsManager")
        .def(py::init<VecList*, int, int, double>())
        .def("update_window_members", &WindowsManager::update_window_members)
        .def_readonly("col_size", &WindowsManager::col_size)
        .def_readonly("row_size", &WindowsManager::row_size)
        .def_readonly("windows", &WindowsManager::windows)
        .def_readonly("capacity", &WindowsManager::capacity)
        .def_readonly("windows_ids", &WindowsManager::windows_ids)
        .def_readonly("window_neighbor", &WindowsManager::window_neighbor)
        ;
    
    py::class_<Solver>(m, "Solver")
        .def(py::init<vector<array<double, 2>>&, vector<array<double, 2>>&, SelfPropellingCfgPy, 
            double, double, int, double>(), py::arg("pos0"), py::arg("vel0"), py::arg("propelling_cfg"), 
            py::arg("size"), py::arg("dt"), py::arg("num_windows"), py::arg("seed")=-1.)
        .def("update_self_propelling", &Solver::update_self_propelling, py::call_guard<py::gil_scoped_release>())
        .def("update_self_propelling_windows", &Solver::update_self_propelling_windows, py::call_guard<py::gil_scoped_release>())
        .def("update_basic", &Solver::update_basic, py::call_guard<py::gil_scoped_release>())
        .def("update_second_law", &Solver::update_second_law, py::call_guard<py::gil_scoped_release>())
        .def("update_arr", &Solver::update_arr, py::call_guard<py::gil_scoped_release>())
        .def("mean_vel", &Solver::mean_vel)
        .def("mean_vel_vec", &Solver::mean_vel_vec)
        .def_readonly("pos", &Solver::pos, byref)
        .def_readonly("vel", &Solver::vel, byref)
        .def_readonly("propelling_vel", &Solver::propelling_vel, byref)
        .def_readonly("propelling_angle", &Solver::propelling_angle, byref)
        .def_readonly("py_pos", &Solver::py_pos, byref)
        .def_readonly("py_vel", &Solver::py_vel, byref)
        .def_readonly("py_propelling_vel", &Solver::py_propelling_vel, byref)
        .def_readonly("py_pos_arr", &Solver::py_pos_arr, byref)
        .def_readonly("rng_manager", &Solver::rng_manager, byref)
        .def_readonly("random_number", &Solver::random_number, byref)
        .def_readonly("sum_forces_matrix_debug", &Solver::sum_forces_matrix_debug, byref)
        .def_readonly("n", &Solver::n, byref)
        ;
}

// PYBIND11_MODULE(example, m) {
//     py::class_<Test>(m, "Test")
//     .def(py::init<vector<array<double, 2>>>())  
//     .def_readonly("pos", &Test::pos, byref)
//     ;
// }