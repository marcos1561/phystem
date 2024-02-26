#include "graph.h"
#include "gui.h"
#include "solver.h"

#include "ui/src/core_application.h"
#include "ui/src/configs/run.h"
// #include "ui/src/configs/graph.h"

using namespace ui::configs;

int main() {
    SolverCfg solver_cfg;
        solver_cfg.dt = 0.001;
        solver_cfg.k = 1;
        
        solver_cfg.pos = PosArray{
            Vec2d{-0.3, 0.6},
            Vec2d{-0.0, 0.4},
            Vec2d{ 0.3, -0.0},
            Vec2d{ 0.0, -0.4},
            Vec2d{ -0.3, -0.6},
        };

        solver_cfg.vel = {0.0, 0.0};

        solver_cfg.numeric_cfg = NumericCfg(200, 0.001);

    RunCfg run_cfg;
        run_cfg.speed = 20;
    
    GraphCfg graph_cfg;
        graph_cfg.color[0] = 1.0;
        graph_cfg.color[1] = 1.0;
        graph_cfg.color[2] = 0.0;
        
        graph_cfg.color_numeric[0] = 1.0;
        graph_cfg.color_numeric[1] = 0.0;
        graph_cfg.color_numeric[2] = 0.0;
        
        graph_cfg.color_analytical[0] = 0.0;
        graph_cfg.color_analytical[1] = 1.0;
        graph_cfg.color_analytical[2] = 0.0;

    auto app = ui::Application<
        Solver, MainGraph, Gui,
        RunCfg, SolverCfg, GraphCfg>
        (run_cfg, solver_cfg, graph_cfg);

    if (app.init() != 0) { return -1; }
    app.run();
}