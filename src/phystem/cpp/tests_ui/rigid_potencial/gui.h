#pragma once

#include "solver.h"
#include "graph.h"

#include "ui/src/core_gui.h"
#include "ui/src/configs/run.h"
// #include "ui/src/configs/graph.h"

// using ui::configs::PointsCfg;
using ui::configs::RunCfg;
using ui::CoreGui;

class Gui: public CoreGui<Solver, GraphCfg, RunCfg> {
public:
    using CoreGui::CoreGui;

    void info() override {
        double sim_dt = solver_timer->mean_time();
        float frame_dt = 1000.0f / io->Framerate;

        ImGui::SeparatorText("Info");
        ImGui::Text("Total : %.3f ms/frame | %.1f FPS", frame_dt, io->Framerate);
        ImGui::Text("Sim   : %.3f ms/passo", sim_dt);
        ImGui::Text("Render: %.3f ms/frame", frame_dt - sim_dt * run_cfg->speed);
        // ImGui::Text("t: %.3f", solver->sim_time);
        // ImGui::Separator();
        // ImGui::Text("dt  : %.3f", solver->get_dt());
        // ImGui::Text("n   : %d", solver->n);
        // ImGui::Text("L   : %.3f", solver->get_size());
        // ImGui::Text("eta : %.3f", solver->get_nabla());
    }

    void control() override {
        ImGui::SeparatorText("Controles");

        float* p1 = &(solver->pos_gui[0][0]); 
        float* p2 = &(solver->pos_gui[1][0]); 
        float* p4 = &(solver->pos_gui[3][0]); 
        float* p5 = &(solver->pos_gui[4][0]); 
        ImGui::SliderFloat2("p1", p1, -1.0, 1.0);
        ImGui::SliderFloat2("p2", p2, -1.0, 1.0);
        ImGui::SliderFloat2("p4", p4, -1.0, 1.0);
        ImGui::SliderFloat2("p5", p5, -1.0, 1.0);

        // ImGui::Checkbox("Demo Window", &state.show_demo_window);      // Edit bools storing our window open/close state

        // if (ImGui::Button("Pause", ImVec2(ImGui::GetContentRegionAvail().x*0.5, 0.0f))) {
        //     state.is_paused = !state.is_paused;
        // }

        // ImGui::SliderInt("Speed", &run_cfg->speed, 1, 40);

        // static bool f_bond;
        // ImGui::Checkbox("F_bond", &f_bond);
        // ImGui::SameLine(0.0, 40.0f);
        // ImGui::Checkbox("F_bend", &f_bond);
        // ImGui::SameLine(0.0, 40.0f);
        // ImGui::Checkbox("F_total", &f_bond);

        // ImGui::ColorEdit3("Point Color", graph_cfg->color); // Edit 3 floats representing a color
    }
};