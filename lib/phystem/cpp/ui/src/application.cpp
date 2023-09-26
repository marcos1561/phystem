#include <iostream>
#include <cmath>
#include <functional>

#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include <glad/glad.h>
#include <GLFW/glfw3.h>

#include "shader_loader.h"
#include "headers/application.h"
#include "headers/gui.h"
#include "headers/main_graph.h"
#include "headers/timer.h"

// #include "solver_test/headers/solver.h"
#include "self_propelling.h"


void proceesInput(GLFWwindow* window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
        glfwSetWindowShouldClose(window, true);
}

int Application::init() {
    // glfw: Initialization and configuration.
    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    auto vid_mode = glfwGetVideoMode(glfwGetPrimaryMonitor());

    float window_scale = 1.3;
    int window_width = vid_mode->width * window_scale;
    int window_height = vid_mode->height * window_scale;

    window = glfwCreateWindow(window_width, window_height, "LearOpenGL", NULL, NULL);
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
    
    info_width = 0.3;
    
    return 0;
}

double get_random() {
    return (double)rand()/(double)RAND_MAX * 2.0 - 1.0;
}

void generate_initial_state(vector<array<double, 2>> &pos, vector<array<double, 2>> &vel, double vo,
    int size, int n) {
    srand(time(0));
    for (int i = 0; i < n; i++) {
        array<double, 2> pi = {size/2.0 * get_random(), size/2.0 * get_random()};

        double angle_i = (double)rand()/(double)RAND_MAX * M_PI * 2;
        array<double, 2> vi = {vo * cos(angle_i), vo * sin(angle_i)};

        pos.push_back(pi);
        vel.push_back(vi);
    }
}

SelfPropelling Application::create_solver() {
    int n = 5000;
    double size = 100;
    double dt = 0.01;
    
    SelfPropellingCfg self_prop_cfg;
    self_prop_cfg.max_attractive_force = 0.75; 
    self_prop_cfg.max_repulsive_force = 30; 
    self_prop_cfg.max_r = 1.0; 
    self_prop_cfg.r_eq = (5. / 6.); 
    self_prop_cfg.mobility = 1;
    self_prop_cfg.relaxation_time = 1;
    self_prop_cfg.vo = 1;
    self_prop_cfg.nabla = 3; 
    // self_prop_cfg.nabla = 4; 

    vector<array<double, 2>> p;
    vector<array<double, 2>> v;
    generate_initial_state(p, v, self_prop_cfg.vo, size, n);

    return SelfPropelling(p, v, self_prop_cfg, size, dt, 10);
}

void Application::run() {
    // Solver solver = Solver(10, 0.01);
    auto solver = create_solver();

    ElementGeometry geo_pos;
    geo_pos.x = info_width;
    geo_pos.y = 0.0f; 
    geo_pos.width = 1.0f - info_width; 
    geo_pos.height = 1.0f; 
    
    MainGraph main_graph(&solver, geo_pos, window);

    main_graph.setup();

    TimeIt timer = TimeIt(100);

    GuiState state;
    state.show_demo_window = false;
    state.speed = 7;
    state.timer = &timer;

    GuiLayout layout;
    layout.info_width = info_width;

    Gui gui(window, io, layout, state, &main_graph.graph_cfg, &solver);

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
            for (int i = 0; i < gui.state.speed; i++)
            {
                timer.start();
                solver.update_windows();
                timer.end();
                // solver->update_normal();
            }
        }
    }
}

void Application::close() {
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwTerminate();
}