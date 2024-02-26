#pragma once

#include <vector>

#include "ui/src/core_graphs.h"
#include "ui/src/configs/graph.h"
#include "solver.h"

using namespace std;
using ui::configs::PointsCfg;
using ui::graphs::CoreMainGraph;

using ui::graphs::shader_dir;
using ui::graphs::SceneObjetcs;

class MainGraph: public CoreMainGraph<SelfPropSolver, PointsCfg> {
public:
    using CoreMainGraph::CoreMainGraph;
private:
    void setup_main() override {
        auto item = RenderItem::Main;

        shaders[item] = Shader((shader_dir + "points/vertex.glsl").c_str(), (shader_dir + "points/fragment.glsl").c_str()); 
        auto& shader = shaders[item];

        scene_obj[item] = SceneObjetcs();
        auto& obj = scene_obj[item]; 

        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);

        pos_vertices = vector<float>(solver->pos.size()*2, 0.0);
        float* vertices = &pos_vertices[0];
        
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void *)0);
        glEnableVertexAttribArray(0);

        ui::check_for_opengl_errors();
    }

    void update_vertices() override {
        for (size_t i = 0; i < solver->pos.size(); i++)
        {
            auto pos_i = solver->pos[i];
            
            pos_i[0] /= solver->get_size() * 0.5;
            pos_i[1] /= solver->get_size() * 0.5;

            pos_vertices[2*i] = pos_i[0];
            pos_vertices[2*i + 1] = pos_i[1];
        }
    }

    void update_main() override {
        auto item = RenderItem::Main;

        update_vertices();

        shaders[item].use();        
        
        shaders[item].setFloat3("color", graph_cfg.color);
        
        glBindVertexArray(scene_obj[item].VAO);
        
        glBindBuffer(GL_ARRAY_BUFFER, scene_obj[item].VBO);
        float* vertices = &pos_vertices[0];
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);
        
        glPointSize(10.0f);
        
        glDrawArrays(GL_POINTS, 0, solver->pos.size());

        // check_for_opengl_errors();
    }
};