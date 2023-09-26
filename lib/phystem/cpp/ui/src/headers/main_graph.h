#pragma once

#include <map>

#include "../shader_loader.h"
#include "graph_cfg.h"
// #include "../solver_test/headers/solver.h"
#include "self_propelling.h"

struct ElementGeometry {
    float x;
    float y;
    float width;
    float height;
};

class MainGraph {    
public:
    GraphCfg graph_cfg;

public:
    MainGraph(SelfPropelling*, ElementGeometry, GLFWwindow*);

    void setup();
    void update();
    
private:
    struct SceneObjetcs
    {
        unsigned int VBO;
        unsigned int VAO;
    };

    enum class RenderItem {Triangle, Points, Border, Background, Main};

private:
    std::map<RenderItem, SceneObjetcs> scene_obj;     
    std::map<RenderItem, Shader> shaders;

    SelfPropelling* solver;
    std::vector<float> pos_vertices;
private:
    void setup_triangle();
    void update_triangle();

    void setup_points();
    void update_points();
    
    void setup_boarder();
    void update_boarder();
  
    void setup_background();
    void update_background();
    
    void setup_main();
    void update_main();
    void update_pos_vertices();

};