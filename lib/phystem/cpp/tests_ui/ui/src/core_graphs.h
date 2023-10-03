#pragma once

#include <map>
#include <vector>

#include "headers/opengl_error.h"
#include "shader_loader.h"
#include "headers/geometry.h"

#include <GLFW/glfw3.h>

namespace ui {

namespace graphs {

const std::string shader_dir = "../ui/src/shaders/";

float get_biggest_square(float width, float height) {
    /**
     * Calcula o lado do maior quadrado que cabe no retângulo 'width' x 'height'
     * de tal forma que o quadrado esteja verticalmente centralizado.
    */
    float side;

    if (height > width) {
        side = width;
    } else {
        side = height;
    }

    return side;
}

using ui::ElementGeometry;

struct SceneObjetcs
{
    unsigned int VBO;
    unsigned int VAO;
};

template<class Solver, class GraphCfg>    
class CoreMainGraph {    
public:
    GraphCfg graph_cfg;
    Solver* solver;
    ElementGeometry el_geo;

public:
    CoreMainGraph() {}

    CoreMainGraph(Solver* solver, GraphCfg graph_cfg, ElementGeometry el_geo, GLFWwindow* window) 
    : solver(solver), graph_cfg(graph_cfg), el_geo(el_geo) {
        static float x = el_geo.x;
        static float y = el_geo.y;
        static float rel_width = el_geo.width;
        static float rel_height = el_geo.height;
        static int x_pad = 40;
        static int y_pad = 40;

        auto framebuffer_size_callback = [] (GLFWwindow* window, int width, int height) -> void {
            float side = get_biggest_square(rel_width * width - 2 * x_pad, rel_height * height - 2 * y_pad);
            glViewport(x * width + x_pad, height - y_pad - side, side, side);
            // glViewport(width * x, 0, width * (1 - x), height);
        };

        int width, height;
        glfwGetFramebufferSize(window, &width, &height);
        framebuffer_size_callback(nullptr, width, height);

        glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);
    }

    void setup() {
        setup_boarder();
        setup_main();
        setup_background();
    }
    
    void update() {
        update_background();
        update_main();
        update_boarder();
    }
    
protected:
    // struct SceneObjetcs
    // {
    //     unsigned int VBO;
    //     unsigned int VAO;
    // };

    enum class RenderItem {Border, Background, Main};

protected:
    std::map<RenderItem, SceneObjetcs> scene_obj;     
    std::map<RenderItem, Shader> shaders;
    
    std::vector<float> pos_vertices;
protected:
    void setup_boarder() {
        shaders[RenderItem::Border] = Shader((shader_dir + "points/vertex.glsl").c_str(), (shader_dir + "points/fragment.glsl").c_str()); 
    
        // Vertex data
        float vertices[] = {
            -1.0f, 1.0f, 1.0f, 1.0f,  
            1.0f, 1.0f, 1.0f, -1.0f,   
            1.0f, -1.0f, -1.0f, -1.0f,	   
            -1.0f, -1.0f, -1.0f, 1.0f,	   
        };

        float color[] = {0.0f, 0.0f, 0.0f};
        shaders[RenderItem::Border].use();
        shaders[RenderItem::Border].setFloat3("color", color);

        scene_obj[RenderItem::Border] = SceneObjetcs();
        auto& obj = scene_obj[RenderItem::Border];

        // Vertex configuration
        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(0);

        ui::check_for_opengl_errors();
    }
    
    void update_boarder() {
        auto item = RenderItem::Border;

        shaders[item].use();        
        
        // shaders[item].setFloat3("color", graph_cfg.color);
        glLineWidth(40.0f);
        glBindVertexArray(scene_obj[item].VAO);
        glDrawArrays(GL_LINES, 0, 16);
    }
  
    void setup_background() {
        auto item = RenderItem::Background;

        shaders[item] = Shader((shader_dir + "points/vertex.glsl").c_str(), (shader_dir + "points/fragment.glsl").c_str()); 
        auto& shader = shaders[item];

        // Vertex data
        float vertices[] = {
            -1.0f,  1.0f, 
             1.0f,  1.0f,  
            -1.0f, -1.0f, 
             1.0f,  1.0f,   
             1.0f, -1.0f, 
            -1.0f, -1.0f,	   
        };

        float color[] = {0.083f*2, 0.06f*2, 0.028f*2};
        shader.use();
        shader.setFloat3("color", color);

        scene_obj[item] = SceneObjetcs();
        auto& obj = scene_obj[item];

        // Vertex configuration
        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(0);

        ui::check_for_opengl_errors();
    }

    void update_background() {
        auto item = RenderItem::Background;

        shaders[item].use();        
        
        // shaders[item].setFloat3("color", graph_cfg.color);
        glBindVertexArray(scene_obj[item].VAO);
        glDrawArrays(GL_TRIANGLES, 0, 6);
    }
    
    virtual void setup_main() = 0;
    virtual void update_main() = 0;
    virtual void update_vertices() = 0;
};

} // namespace graphs
} // namespace ui
