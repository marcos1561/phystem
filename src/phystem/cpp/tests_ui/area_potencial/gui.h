#pragma once

#include <cmath>

#include "solver.h"
#include "graph.h"

#include "ui/src/core_gui.h"
#include "ui/src/configs/run.h"

using ui::configs::RunCfg;
using ui::CoreGui;

class Gui: public CoreGui<Solver, GraphCfg, RunCfg> {
public:
    using CoreGui::CoreGui;

    void info() override {
        double sim_dt = solver_timer->mean_time();
        float frame_dt = 1000.0f / io->Framerate;

        auto rs = point_radius();
        double r_point = rs[0]; 
        double r_target = rs[1];

        ImGui::SeparatorText("Info");
        ImGui::Text("Total : %.3f ms/frame | %.1f FPS", frame_dt, io->Framerate);
        ImGui::Text("Sim   : %.3f ms/passo", sim_dt);
        ImGui::Text("Render: %.3f ms/frame", frame_dt - sim_dt * run_cfg->speed);
        ImGui::Text("Time  : %.3f s", solver->time);
        ImGui::NewLine();
        ImGui::Text("Area_0  : %.3f", solver->calc_area_0(solver->pos));
        ImGui::Text("Area    : %.3f", solver->calc_area(solver->pos));
        ImGui::NewLine();
        ImGui::Text("r_point  : %.3f", r_point);
        ImGui::Text("r_target : %.3f", r_target);
    }

    void control() override {
        ImGui::SeparatorText("Controles");
        ImGui::SliderFloat("p_0", &solver->p_0, 0.0001, 10.0);
    }

    Vec2d point_radius() {
        auto& p = solver->pos[solver->point_id];
        
        int other_id = 0;
        if (other_id == solver->point_id)
            other_id = 1;

        auto& other_p = solver->pos[other_id];

        return {sqrt(p[0]*p[0] + p[1]*p[1]), sqrt(other_p[0]*other_p[0] + other_p[1]*other_p[1])};
    }
};