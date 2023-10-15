#include "graph.h"
#include "gui.h"
#include "solver.h"

#include "ui/src/core_application.h"
#include "ui/src/configs/run.h"

using namespace ui::configs;

void circle_points(SolverCfg& cfg, double radius, int n) {
    cfg.point_id = 0;
    cfg.p_0 = 3.544907701;

    double init_angle = 2 * M_PI / (double)n;

    cfg.pos = PosArray(n);
    
    double angle, x, y;

    // double angle = init_angle / 2.0;
    // double x = radius * cos(angle) / 2.0;
    // double y = radius * sin(angle) / 2.0;
    cfg.pos[0] = {2*radius, 0};

    for (int i = 1; i < n; i++)
    {
        angle = 2.0 * M_PI / (double)n * (double)i;
        x = radius * cos(angle);
        y = radius * sin(angle);

        cfg.pos[i] = {x, y};
    }
}

void square_points(SolverCfg cfg, double side, Vec2d point_pos = {0.0, 0.0}) {
    cfg.point_id = 0;
    cfg.pos = PosArray{
            point_pos,
            Vec2d{-side/2.0, -side/2.0},
            Vec2d{ side/2.0, -side/2.0},
            Vec2d{ side/2.0,  side/2.0},
        };
}

int main() {
    SolverCfg solver_cfg;
        solver_cfg.dt = 0.001;
        
        // circle_points(solver_cfg, 0.4, 10);

        solver_cfg.point_id = 3;
        solver_cfg.pos = PosArray{
            Vec2d{-0.3,  0.3},
            Vec2d{-0.3, -0.3},
            Vec2d{ 0.3, -0.3},
            Vec2d{ 0.3,  0.3},
        };
        solver_cfg.p_0 = 4.8284271; // Triângulo retângulo com catetos iguais.
        // solver_cfg.p_0 = 3.544907701; // Círculo.
        
        // solver_cfg.point_id = 0;
        // solver_cfg.pos = PosArray{
        //     Vec2d{0.0,  0.0},
        //     Vec2d{-0.3, -0.3},
        //     Vec2d{ 0.3, -0.3},
        // };
        // solver_cfg.p_0 = 4.8284271; // Triângulo retângulo com catetos iguais.

        solver_cfg.vel = {0.0, 0.0};
        solver_cfg.k = 1.0;

    NumericCfg numeric_cfg;
        numeric_cfg.dr = 0.0001;
    solver_cfg.numeric_cfg = numeric_cfg;

    RunCfg run_cfg;
        run_cfg.speed = 100;
    
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

        graph_cfg.line_width = 5.0;

    auto app = ui::Application<
        Solver, MainGraph, Gui,
        RunCfg, SolverCfg, GraphCfg>
        (run_cfg, solver_cfg, graph_cfg);

    if (app.init() != 0) { return -1; }
    app.run();
}