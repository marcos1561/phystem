#pragma once

#include "graph2.h"
#include "gui.h"
#include "solver.h"

#include "ui/src/core_application.h"
#include "ui/src/configs/run.h"
#include "ui/src/configs/graph.h"

class Application : public 
    ui::Application<SelfPropSolver, MainGraph, Gui, 
                        RunCfg, SolverCfg, PointsCfg> 
{ 
    using ui::Application<SelfPropSolver, MainGraph, Gui, 
                        RunCfg, SolverCfg, PointsCfg>::Application; 

    SelfPropSolver create_solver() override {
        vector<array<double, 2>> p;
        vector<array<double, 2>> v;
        generate_initial_state(p, v,
            solver_cfg.dynamic_cfg.vo, solver_cfg.size, solver_cfg.n);
        
        return SelfPropSolver(
            p, v, solver_cfg.dynamic_cfg, solver_cfg.size, solver_cfg.dt,
            solver_cfg.num_cols_windows, solver_cfg.seed);
    }
};