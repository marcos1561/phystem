#pragma once

#include <iostream>
#include <cmath>
#include <functional>

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <glad/glad.h>
#include <GLFW/glfw3.h>

// #include "shader_loader.h"

#include "headers/timer.h"
#include "headers/geometry.h"
#include "configs/layout.h"

// #include "solver_test/headers/solver.h"
// #include "self_propelling.h"


namespace ui {

void proceesInput(GLFWwindow* window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
        glfwSetWindowShouldClose(window, true);
}

template<class Solver, class MainGraph, class Gui,
    class RunCfg, class SolverCfg, class GraphCfg, class LayoutCfg=configs::LayoutCfg>
class Application {
protected:
    RunCfg run_cfg;
    SolverCfg solver_cfg;
    GraphCfg graph_cfg; 
    LayoutCfg layout_cfg;

    // Solver solver;
    // MainGraph main_graph;
    // Gui gui;

    GLFWwindow* window;
    ImGuiIO* io;
    TimeIt solver_timer;

public:
    Application(RunCfg run_cfg, SolverCfg solver_cfg, GraphCfg graph_cfg, LayoutCfg layout_cfg=LayoutCfg())
    : run_cfg(run_cfg), solver_cfg(solver_cfg), graph_cfg(graph_cfg), layout_cfg(layout_cfg) {
        // if (layout_cfg == nullptr) {
        //     layout_cfg = configs::LayoutCfg();
        // }
    };

    int init() {
        // glfw: Initialization and configuration.
        glfwInit();
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

        auto vid_mode = glfwGetVideoMode(glfwGetPrimaryMonitor());

        float window_scale = layout_cfg.windows_scale;
        int window_width = vid_mode->width * window_scale;
        int window_height = vid_mode->height * window_scale;

        window = glfwCreateWindow(window_width, window_height, "Phystem", NULL, NULL);
        if (window == NULL) {
            std::cout << "Failed to create GLFW window." << std::endl;
            glfwTerminate();
            return -1; 
        }
        glfwMakeContextCurrent(window);
        
        // glad: Load all OpenGL function pointers
        if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress))
        {
            std::cout << "Failed to initialize GLAD." << std::endl;
            return -1;
        }

        // Setup Dear ImGui context
        IMGUI_CHECKVERSION();
        ImGui::CreateContext();
        io = &ImGui::GetIO();
        io->ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;     // Enable Keyboard Controls
        io->ConfigFlags |= ImGuiConfigFlags_NavEnableGamepad;      // Enable Gamepad Controls

        // Setup Platform/Renderer backends
        ImGui_ImplGlfw_InitForOpenGL(window, true);          // Second param install_callback=true will install GLFW callbacks and chain to existing ones.
        ImGui_ImplOpenGL3_Init("#version 330 core");
        
        return 0;
    };

    virtual Solver create_solver() {
        return Solver(solver_cfg);
    };
    
    Gui create_gui(Solver& solver, MainGraph& main_graph) {
        return Gui(window, io, &layout_cfg.gui_layout, &solver_timer, &main_graph.graph_cfg, 
            &run_cfg, &solver);
    }

    MainGraph create_main_graph(Solver& solver) {
        ui::ElementGeometry geo_pos;
        geo_pos.x = layout_cfg.gui_layout.info_width;
        geo_pos.y = 0.0f; 
        geo_pos.width = 1.0f - layout_cfg.gui_layout.info_width; 
        geo_pos.height = 1.0f;

        return MainGraph(&solver, graph_cfg, geo_pos, window);
    }

    void run() {
        /**
         * TODO: Olhar como utilizar a operação 'move'
         * para ter solver, main_graph, gui como membros dessa
         * classe, mas inicializar eles em funções separadas.
         * 
         * O problema atual é a copia que acontece caso tais
         * variáveis sejam membros da classe, por exemplo
         * 
         * solver = create_solver();
         * 
         * Causa uma cópia que vai invalidar o ponteiro dentro
         * do windows_manager.
        */
        solver_timer = TimeIt(100);
        
        Solver solver = create_solver();
        // solver.update_windows_manager_pointer();

        MainGraph main_graph = create_main_graph(solver);
        Gui gui = create_gui(solver, main_graph);

            
        main_graph.setup();
        while (!glfwWindowShouldClose(window)) {
            // Input
            glfwPollEvents();
            proceesInput(window);

            // Start the Dear ImGui frame
            gui.init_frame();
            gui.show();

            // Rendering
            // glClearColor(0.083f*2, 0.06f*2, 0.028f*2, 1.0f);
            glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
            glClear(GL_COLOR_BUFFER_BIT);
            main_graph.update();

            gui.render_frame();       

            // Swap buffer
            glfwSwapBuffers(window);

            if (!gui.state.is_paused) {
                for (int i = 0; i < gui.run_cfg->speed; i++)
                {
                    solver_timer.start();
                    solver.update();
                    solver_timer.end();
                    // solver->update_normal();
                }
            }
        }
    }

    void close() {
        ImGui_ImplOpenGL3_Shutdown();
        ImGui_ImplGlfw_Shutdown();
        ImGui::DestroyContext();
        glfwTerminate();
    };
};

} // namespace ui