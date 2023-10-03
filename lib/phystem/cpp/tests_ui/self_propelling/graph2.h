#pragma once

#include "ui/src/graphs/points_graph.h"
#include "ui/src/configs/graph.h"
#include "solver.h"

using ui::graphs::PointsGraph;
using ui::configs::PointsCfg;

class MainGraph : public PointsGraph<SelfPropSolver, PointsCfg> {
    using PointsGraph::PointsGraph;

    void transform(array<double, 2>& pos) override {
        pos[0] /= solver->get_size() * 0.5;
        pos[1] /= solver->get_size() * 0.5;
    }
};