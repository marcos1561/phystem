#pragma once

#include <array>
#include "solver.h"

#include "ui/src/core_graphs.h"

using ui::graphs::CoreMainGraph;
using ui::graphs::SceneObjetcs;

const std::string shader_dir = "../area_potencial/shaders/";

struct GraphCfg {
    float color[3];
    float color_numeric[3];
    float color_analytical[3];
    float line_width;
};

class MainGraph : public CoreMainGraph<Solver, GraphCfg> {
public:
    using CoreMainGraph<Solver, GraphCfg>::CoreMainGraph;

    std::vector<float> points_vertices;

private:
    enum class RenderItem {
        Main, Points
    };

    std::map<RenderItem, SceneObjetcs> scene_obj;     
    std::map<RenderItem, Shader> shaders; 

    void setup_lines() {
        auto item = RenderItem::Main;

        shaders[item] = Shader((ui::graphs::shader_dir + "points/vertex.glsl").c_str(), 
                                             (ui::graphs::shader_dir + "points/fragment.glsl").c_str()); 
    
        // float color[] = {0.0f, 0.0f, 0.0f};
        float *color = graph_cfg.color;
        shaders[item].use();
        shaders[item].setFloat3("color", color);

        scene_obj[item] = SceneObjetcs();
        auto& obj = scene_obj[item];

        // Vertex configuration
        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        pos_vertices = std::vector<float>(solver->pos.size() * 4, 0.0);
        float* vertices = &pos_vertices[0];

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW);
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(0);

        ui::check_for_opengl_errors();
    }

    void setup_points() {
        auto item = RenderItem::Points;

        shaders[item] = Shader((shader_dir + "vertex.glsl").c_str(), 
                                (shader_dir + "fragment.glsl").c_str()); 
    
        // float color[] = {0.0f, 0.0f, 0.0f};
        shaders[item].use();

        scene_obj[item] = SceneObjetcs();
        auto& obj = scene_obj[item];

        // Vertex configuration
        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        points_vertices = std::vector<float>((2 + 3) * 2, 0.0);
        
        // Analytical point color
        points_vertices[2] = 0.0;
        points_vertices[3] = 1.0;
        points_vertices[4] = 0.0;
        
        // Numeric point color
        points_vertices[7] = 1.0;
        points_vertices[8] = 0.0;
        points_vertices[9] = 0.0;

        float* vertices = &points_vertices[0];

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW);
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)0);
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void *)(2 * sizeof(float)));
        glEnableVertexAttribArray(0);
        glEnableVertexAttribArray(1);

        ui::check_for_opengl_errors();
    }

    void update_lines() {
        auto item = RenderItem::Main;

        shaders[item].use();        

        glLineWidth(graph_cfg.line_width);

        glBindVertexArray(scene_obj[item].VAO);
        
        glBindBuffer(GL_ARRAY_BUFFER, scene_obj[item].VBO);
        float* vertices = &pos_vertices[0];
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);
        glDrawArrays(GL_LINES, 0, pos_vertices.size());

        ui::check_for_opengl_errors();
    }
    
    void update_points() {
        auto item = RenderItem::Points;

        shaders[item].use();        

        glBindVertexArray(scene_obj[item].VAO);
        
        glPointSize(20.0f);

        glBindBuffer(GL_ARRAY_BUFFER, scene_obj[item].VBO);
        float* vertices = &points_vertices[0];
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * points_vertices.size(), vertices, GL_DYNAMIC_DRAW);
        glDrawArrays(GL_POINTS, 0, 2);

        ui::check_for_opengl_errors();
    }
    
    void setup_main() override {
        setup_lines();
        setup_points();
    }

    void update_main() override {
        update_vertices();
        
        update_lines();
        update_points();
    }

    void update_vertices() override {
        // Points
        points_vertices[0] = solver->pos[solver->point_id][0]; 
        points_vertices[1] = solver->pos[solver->point_id][1];
        
        points_vertices[5] = solver->pos_numeric[0]; 
        points_vertices[6] = solver->pos_numeric[1];
        

        for (std::size_t i = 0; i < solver->pos.size()-1; i++) {
            auto pos1 = solver->pos[i];
            auto pos2 = solver->pos[i+1];
            
            int start_id = i * 4; 

            pos_vertices[start_id] = pos1[0]; 
            pos_vertices[start_id+1] = pos1[1]; 
            
            pos_vertices[start_id+2] = pos2[0]; 
            pos_vertices[start_id+3] = pos2[1]; 
        }
        
        int i = solver->pos.size() - 1;
        int start_id = i * 4; 
        
        auto pos1 = solver->pos[i];
        auto pos2 = solver->pos[0];
        
        pos_vertices[start_id] = pos1[0]; 
        pos_vertices[start_id+1] = pos1[1]; 
        
        pos_vertices[start_id+2] = pos2[0]; 
        pos_vertices[start_id+3] = pos2[1]; 
    }
};