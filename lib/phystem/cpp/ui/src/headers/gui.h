#pragma once

#include "graph_cfg.h"
#include "self_propelling.h"
#include "timer.h"

struct GuiLayout {
    float info_width;
};

struct GuiState {
    bool show_demo_window;
    int speed;
    float is_paused;
    TimeIt* timer;

    GuiState () {is_paused = false;}
};

class Gui {
public:
    GLFWwindow* window;
    ImGuiIO* io;

    GuiLayout layout;
    GuiState state;

    GraphCfg* graph_cfg;
    SelfPropelling* solver;

public:
    Gui(GLFWwindow* window, ImGuiIO* io, GuiLayout layout, GuiState state, GraphCfg* graph_cfg, SelfPropelling* solver);

    void init_frame();
    void render_frame();

    void show();
    void info();
    void control();
};