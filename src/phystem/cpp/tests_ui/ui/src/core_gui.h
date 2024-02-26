#pragma once

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include "configs/layout.h"
#include "headers/timer.h"

#include "GLFW/glfw3.h"

namespace ui {

template<class Solver, class GraphCfg, class RunCfg, class GuiLayout=configs::GuiLayout>
class CoreGui {
public:
    GLFWwindow* window;
    ImGuiIO* io;

    GuiLayout* layout;
    TimeIt* solver_timer;

    GraphCfg* graph_cfg;
    RunCfg* run_cfg;
    Solver* solver;

public:
    struct State {
        bool show_demo_window;
        bool is_paused;
    };

    State state;

public:
    CoreGui() {}

    CoreGui(GLFWwindow* window, ImGuiIO* io, GuiLayout* layout, TimeIt* solver_timer, GraphCfg* graph_cfg, RunCfg* run_cfg,  Solver* solver)
    : window(window), io(io), layout(layout), solver_timer(solver_timer), graph_cfg(graph_cfg), 
        run_cfg(run_cfg), solver(solver) 
    { 
        io->FontGlobalScale = 3.0;

        ImGuiStyle& style = ImGui::GetStyle();
        style.ItemSpacing.y = 8;

        state.show_demo_window = false;
        state.is_paused = false;
    }

    void init_frame() {
        // Start the Dear ImGui frame
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();
    }

    void render_frame() {
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    }

    void show() {
        int width, height;
        glfwGetFramebufferSize(window, &width, &height);
        ImGui::SetNextWindowPos(ImVec2(0, 0));
        ImGui::SetNextWindowSize(ImVec2(layout->info_width * width, height));
        
        ImGuiWindowFlags window_flags = 0;
        window_flags |= ImGuiWindowFlags_NoTitleBar;

        static bool p_open = true;
        ImGui::Begin("Noice", &p_open, window_flags);                          // Create a window called "Hello, world!" and append into it.
        info();
        control();

        if (state.show_demo_window)
            ImGui::ShowDemoWindow(&state.show_demo_window);

        ImGui::End();
    }
    
    virtual void info() = 0;
    virtual void control() = 0;
};

} // namespace ui