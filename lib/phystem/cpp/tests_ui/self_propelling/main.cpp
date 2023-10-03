#include "solver.h"
#include "application.h"

#include "ui/src/configs/run.h"
#include "ui/src/configs/graph.h"
#include "../../src/configs/self_propelling.h"

using namespace ui::configs;

int main() {
    SolverCfg solver_cfg;
    
    solver_cfg.dt = 0.01;
    solver_cfg.size = 80;
    solver_cfg.n = 2000;
    solver_cfg.seed = -1;

    solver_cfg.num_cols_windows = 10;

    SelfPropellingCfg self_prop_cfg;
        self_prop_cfg.max_attractive_force = 0.75; 
        self_prop_cfg.max_repulsive_force = 30; 
        self_prop_cfg.max_r = 1.0; 
        self_prop_cfg.r_eq = (5. / 6.); 
        self_prop_cfg.mobility = 1;
        self_prop_cfg.relaxation_time = 1;
        self_prop_cfg.vo = 1;
        self_prop_cfg.nabla = 1; 

    solver_cfg.dynamic_cfg = self_prop_cfg;

    PointsCfg graph_cfg;

    RunCfg run_cfg;
        run_cfg.speed = 10;
   

    Application app(run_cfg, solver_cfg, graph_cfg);
    if (app.init() != 0) { return -1;}

    app.run();
    app.close();

    return 0;
}