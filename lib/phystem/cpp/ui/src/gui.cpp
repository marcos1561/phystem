#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include "headers/gui.h"
#include <GLFW/glfw3.h>

Gui::Gui(GLFWwindow* window, ImGuiIO* io, GuiLayout layout, GuiState state, GraphCfg* graph_cfg, SelfPropelling* solver)
    : window(window), io(io), layout(layout), state(state), graph_cfg(graph_cfg), solver(solver) 
    { 
        io->FontGlobalScale = 3.0;

        ImGuiStyle& style = ImGui::GetStyle();
        style.ItemSpacing.y = 8;
    };

void Gui::show() {
    int width, height;
    glfwGetFramebufferSize(window, &width, &height);
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(ImVec2(layout.info_width * width, height));
    
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

void Gui::info() {
    ImGui::SeparatorText("Info");
    ImGui::Text("%.3f ms/frame | %.1f FPS", 1000.0f / io->Framerate, io->Framerate);
    ImGui::Text("%.3f ms/passo", state.timer->mean_time());
    ImGui::Text("t: %.3f", solver->sim_time);
    ImGui::Separator();
    ImGui::Text("dt  : %.3f", solver->get_dt());
    ImGui::Text("n   : %d", solver->n);
    ImGui::Text("L   : %.3f", solver->get_size());
    ImGui::Text("eta : %.3f", solver->get_nabla());
}

void Gui::control() {
    ImGui::SeparatorText("Controles");

    ImGui::Checkbox("Demo Window", &state.show_demo_window);      // Edit bools storing our window open/close state

    if (ImGui::Button("Pause", ImVec2(ImGui::GetContentRegionAvail().x*0.5, 0.0f))) {
        state.is_paused = !state.is_paused;
    }

    ImGui::SliderInt("Speed", &state.speed, 1, 40);

    static bool f_bond;
    ImGui::Checkbox("F_bond", &f_bond);
    ImGui::SameLine(0.0, 40.0f);
    ImGui::Checkbox("F_bend", &f_bond);
    ImGui::SameLine(0.0, 40.0f);
    ImGui::Checkbox("F_total", &f_bond);

    ImGui::ColorEdit3("Point Color", graph_cfg->color); // Edit 3 floats representing a color
}

void Gui::init_frame() {
    // Start the Dear ImGui frame
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
}

void Gui::render_frame() {
    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}