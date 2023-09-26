#pragma once

#include "imgui.h"
// #include "imgui_impl_glfw.h"
// #include "imgui_impl_opengl3.h"

// #include <glad/glad.h>
#include <GLFW/glfw3.h>

#include "self_propelling.h"

class Application {
private:
    GLFWwindow* window;
    ImGuiIO* io;

    float info_width;

public:
    Application() {};

    int init();
    SelfPropelling create_solver();
    void run();
    void close();
};