#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

#include "../src/solvers/self_propelling.h"
#include "../src/solvers/ring.h"
#include "../src/configs/python_configs.h"

using namespace std;

PYBIND11_MAKE_OPAQUE(vector<vector<array<double, 2>>>);
PYBIND11_MAKE_OPAQUE(vector<array<double, 2>>);
PYBIND11_MAKE_OPAQUE(vector<vector<vector<double*>>>);
PYBIND11_MAKE_OPAQUE(vector<vector<double*>>);
PYBIND11_MAKE_OPAQUE(vector<vector<double>>);
PYBIND11_MAKE_OPAQUE(vector<double>);
PYBIND11_MAKE_OPAQUE(vector<int>);
PYBIND11_MAKE_OPAQUE(vector<unsigned long int>);

using List = vector<double>;
using List2d = vector<vector<double>>;
using VecList = vector<array<double, 2>>;
using PyVecList = vector<vector<double*>>;
using PyVecList3d = vector<vector<vector<double*>>>;

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
    py::bind_vector<vector<int>>(data_types, "ListInt");
    py::bind_vector<vector<bool>>(data_types, "ListBool");
    py::bind_vector<Vector3d>(data_types, "Vector3d");
    py::bind_vector<VecList>(data_types, "PosVec");
    py::bind_vector<List>(data_types, "List");
    py::bind_vector<List2d>(data_types, "List2d");
    py::bind_vector<PyVecList>(data_types, "PyVecList");
    py::bind_vector<PyVecList3d>(data_types, "PyVecList3d");
    py::bind_vector<vector<unsigned long int>>(data_types, "VecUInt");
    py::bind_vector<vector<InPolChecker::ColInfo>>(data_types, "ListColInfo");

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
    
    py::enum_<RingIntegrationType>(configs, "RingIntegrationType")
        .value("euler", RingIntegrationType::euler)
        .value("verlet", RingIntegrationType::verlet)
        .value("rk4", RingIntegrationType::rk4)
        ;

    py::enum_<RingUpdateType>(configs, "RingUpdateType")
        .value("periodic_borders", RingUpdateType::periodic_borders)
        .value("stokes", RingUpdateType::stokes)
        .value("invagination", RingUpdateType::invagination)
        ;

    py::class_<StokesCfgPy>(configs, "StokesCfgPy")
        .def(py::init<py::dict &>())
        ;
    
    py::class_<StokesCfg>(configs, "StokesCfg")
        .def(py::init())
        .def_readonly("obstacle_r", &StokesCfg::obstacle_r)
        .def_readonly("obstacle_x", &StokesCfg::obstacle_x)
        .def_readonly("obstacle_y", &StokesCfg::obstacle_y)
        .def_readonly("create_length", &StokesCfg::create_length)
        .def_readonly("remove_length", &StokesCfg::remove_length)
        .def_readonly("num_max_rings", &StokesCfg::num_max_rings)
        ;
    
    py::class_<ParticleWindowsCfg>(configs, "ParticleWindowsCfg")
        .def(py::init<int, int, int>())
        .def_readonly("num_cols", &ParticleWindowsCfg::num_cols)
        .def_readonly("num_rows", &ParticleWindowsCfg::num_rows)
        .def_readonly("update_freq", &ParticleWindowsCfg::update_freq)
        ;
    
    py::class_<InPolCheckerCfg>(configs, "InPolCheckerCfg")
        .def(py::init<int, int, int, int, bool>())
        ;

    //==
    // Manager
    //==
    py::class_<RngManager>(managers, "RngManager")
        .def(py::init<int>())
        .def_readonly("random_nums", &RngManager::random_nums, byref)
        ;

    py::class_<SpaceInfo>(managers, "SpaceInfo")
        .def(py::init<double, double, std::array<double, 2>>());

    py::class_<WindowsManager>(managers, "WindowsManager")
        .def(py::init<VecList*, vector<int>*, int*,  int, int, SpaceInfo>())
        .def("update_window_members", &WindowsManager::update_window_members)
        .def_readonly("col_size", &WindowsManager::col_size)
        .def_readonly("row_size", &WindowsManager::row_size)
        .def_readonly("windows", &WindowsManager::windows)
        .def_readonly("capacity", &WindowsManager::capacity)
        .def_readonly("windows_ids", &WindowsManager::windows_ids)
        .def_readonly("windows_center", &WindowsManager::windows_center)
        .def_readonly("window_neighbor", &WindowsManager::window_neighbor)
        ;
    
    py::class_<WindowsManagerRing>(managers, "WindowsManagerRing")
        .def(py::init<vector<vector<array<double, 2>>>*, vector<int>*, int*, int, int, SpaceInfo>())
        .def("update_window_members", &WindowsManagerRing::update_window_members)
        .def("get_window_elements", &WindowsManagerRing::get_window_elements)
        .def_readonly("col_size", &WindowsManagerRing::col_size)
        .def_readonly("row_size", &WindowsManagerRing::row_size)
        .def_readonly("windows", &WindowsManagerRing::windows)
        .def_readonly("capacity", &WindowsManagerRing::capacity)
        .def_readonly("windows_ids", &WindowsManagerRing::windows_ids)
        .def_readonly("window_neighbor", &WindowsManagerRing::window_neighbor)
        .def_readonly("window_length", &WindowsManagerRing::window_length)
        .def_readonly("window_height", &WindowsManagerRing::window_height)
        .def_readonly("col_size", &WindowsManagerRing::col_size)
        .def_readonly("row_size", &WindowsManagerRing::row_size)
        ;
    
    py::class_<InPolChecker::ColInfo>(managers, "ColInfo")
        .def(py::init<int, int, int>())
        .def_readonly("ring_id", &InPolChecker::ColInfo::ring_id)
        .def_readonly("p_id", &InPolChecker::ColInfo::p_id)
        .def_readonly("col_ring_id", &InPolChecker::ColInfo::col_ring_id)
        ;

    py::class_<InPolChecker>(managers, "InPolChecker")
        .def(py::init<Vector3d*, VecList*, vector<int>*, int*, int, int, double, bool>())
        .def_readonly("num_inside_points", &InPolChecker::num_inside_points)
        .def_readonly("inside_points", &InPolChecker::inside_points)
        .def_readonly("collisions", &InPolChecker::collisions)
        .def_readonly("is_col_resolved", &InPolChecker::is_col_resolved)
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
    
    py::class_<SpringDebug>(solvers, "SpringDebug")
        .def_readonly("count_overlap", &SpringDebug::count_overlap)
        ;      
    py::class_<ExcludedVolDebug>(solvers, "ExcludedVolDebug")
        .def_readonly("count_overlap", &ExcludedVolDebug::count_overlap)
        ;      
    py::class_<AreaDebug>(solvers, "AreaDebug")
        .def_readonly("count_overlap", &AreaDebug::count_overlap)
        .def_readonly("area", &AreaDebug::area, byref)
        ;      
    py::class_<UpdateDebug>(solvers, "UpdateDebug")
        .def_readonly("count_zero_speed", &UpdateDebug::count_zero_speed)
        .def_readonly("high_vel", &UpdateDebug::high_vel)
        ;      

    py::class_<Ring>(solvers, "Ring")
        .def(py::init<Vector3d&, vector<double>&, int, RingCfgPy,
            double, double, double, ParticleWindowsCfg, RingUpdateType, RingIntegrationType, 
            StokesCfgPy, InPolCheckerCfg, double>(),
            py::arg("pos0"), py::arg("self_prop_angle0"), py::arg("num_particles"),  
            py::arg("dynamic_cfg"), py::arg("height"), py::arg("length"), py::arg("dt"), 
            py::arg("particle_windows_cfg"), py::arg("update_type"), py::arg("integration_type"), 
            py::arg("stokes_cfg"), py::arg("InPolChecker"), py::arg("seed")=-1)
        .def("update_normal", &Ring::update_normal, py::call_guard<py::gil_scoped_release>())
        .def("update_windows", &Ring::update_windows, py::call_guard<py::gil_scoped_release>())
        .def("update_stokes", &Ring::update_stokes, py::call_guard<py::gil_scoped_release>())
        .def("update_visual_aids", &Ring::update_visual_aids, py::call_guard<py::gil_scoped_release>())
        .def("init_invagination", &Ring::init_invagination, py::call_guard<py::gil_scoped_release>())
        .def("load_checkpoint", &Ring::load_checkpoint, py::call_guard<py::gil_scoped_release>())
        .def("get_particle_id", &Ring::get_particle_id, py::call_guard<py::gil_scoped_release>())
        .def_readwrite("sim_time", &Ring::sim_time, byref)
        .def_readwrite("num_time_steps", &Ring::num_time_steps, byref)
        .def_readonly("num_max_rings", &Ring::num_max_rings, byref)
        .def_readonly("num_particles", &Ring::num_particles, byref)
        .def_readonly("num_active_rings", &Ring::num_active_rings, byref)
        .def_readonly("rings_ids", &Ring::rings_ids, byref)
        .def_readonly("pos", &Ring::pos, byref)
        .def_readonly("vel", &Ring::vel, byref)
        .def_readonly("self_prop_angle", &Ring::self_prop_angle, byref)
        .def_readonly("unique_rings_ids", &Ring::unique_rings_ids, byref)
        .def_readonly("stokes_cfg", &Ring::stokes_cfg, byref)
        .def_readonly("pos_continuos", &Ring::pos_continuos, byref)
        .def_readonly("pos_t", &Ring::pos_t, byref)
        .def_readonly("graph_points", &Ring::graph_points, byref)
        .def_readonly("update_debug", &Ring::update_debug)
        .def_readonly("spring_debug", &Ring::spring_debug)
        .def_readonly("excluded_vol_debug", &Ring::excluded_vol_debug)
        .def_readonly("area_debug", &Ring::area_debug)
        .def_readonly("spring_forces", &Ring::spring_forces)
        .def_readonly("self_prop_vel", &Ring::self_prop_vel)
        .def_readonly("total_forces", &Ring::sum_forces_matrix)
        // .def_readonly("total_forces", &Ring::total_forces)
        .def_readonly("vol_forces", &Ring::vol_forces)
        .def_readonly("area_forces", &Ring::area_forces)
        .def_readonly("format_forces", &Ring::format_forces)
        .def_readonly("invasion_forces", &Ring::invasion_forces)
        .def_readonly("obs_forces", &Ring::obs_forces)
        .def_readonly("creation_forces", &Ring::creation_forces)
        .def_readonly("differences", &Ring::differences)
        .def_readonly("center_mass", &Ring::center_mass)
        .def_readonly("in_pol_checker", &Ring::in_pol_checker)
        .def_readonly("num_created_rings", &Ring::num_created_rings)
        .def_readonly("windows_manager", &Ring::windows_manager)
        ;
}