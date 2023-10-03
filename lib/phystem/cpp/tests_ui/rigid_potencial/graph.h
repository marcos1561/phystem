#pragma once

#include <array>
#include "solver.h"

// #include "ui/src/graphs/points_graph.h"
// #include "ui/src/configs/graph.h"
#include "ui/src/core_graphs.h"

using ui::graphs::CoreMainGraph;
using ui::graphs::SceneObjetcs;
// using ui::configs::PointsCfg;

// class MainGraph : public PointsGraph<Solver, PointsCfg> {
//     using PointsGraph::PointsGraph;

//     void transform(std::array<double, 2>& pos) override { }
// }; 

struct GraphCfg {
    float color[3];
    float color_numeric[3];
    float color_analytical[3];
};

const std::string shader_dir = "../rigid_potencial/shaders/";

class MainGraph : public CoreMainGraph<Solver, GraphCfg> {
public:
    using CoreMainGraph<Solver, GraphCfg>::CoreMainGraph;

private:
    void setup_main() override {
        auto item = CoreMainGraph<Solver, GraphCfg>::RenderItem::Main;

        this->shaders[item] = Shader((shader_dir + "vertex.glsl").c_str(), (shader_dir + "fragment.glsl").c_str()); 
        auto& shader = this->shaders[item];

        this->scene_obj[item] = SceneObjetcs();
        auto& obj = this->scene_obj[item]; 

        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);

        this->pos_vertices = std::vector<float>(this->solver->pos.size()*(2 + 3) + 5, 0.0);
        float* vertices = &this->pos_vertices[0];
        
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * this->pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void *)0);
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void *)(2 * sizeof(float)));
        glEnableVertexAttribArray(0);
        glEnableVertexAttribArray(1);

        ui::check_for_opengl_errors();
    }

    // virtual void transform(std::array<double, 2>& pos) = 0;
    // Transforma a coordenada dada para o espaço da renderização.

    void update_vertices() override {
        this->pos_vertices[0] = solver->pos_numeric[0];
        this->pos_vertices[1] = solver->pos_numeric[1];
            
        auto color = graph_cfg.color_numeric;
        this->pos_vertices[2] = color[0]; 
        this->pos_vertices[3] = color[1];
        this->pos_vertices[4] = color[2];
        
        for (std::size_t i = 0; i < this->solver->pos.size(); i++)
        {
            auto pos_i = this->solver->pos[i];
            
            // transform(pos_i);

            std::size_t start = 5*(i + 1);

            this->pos_vertices[start] = pos_i[0];
            this->pos_vertices[start + 1] = pos_i[1];
                
            color = graph_cfg.color;
            if (i == 2)
                color = graph_cfg.color_analytical;

            this->pos_vertices[start + 2] = color[0]; 
            this->pos_vertices[start + 3] = color[1];
            this->pos_vertices[start + 4] = color[2];
        }
    }

    void update_main() override {
        auto item = CoreMainGraph<Solver, GraphCfg>::RenderItem::Main;

        update_vertices();

        this->shaders[item].use();        
        
        glBindVertexArray(this->scene_obj[item].VAO);
        
        glBindBuffer(GL_ARRAY_BUFFER, this->scene_obj[item].VBO);
        float* vertices = &this->pos_vertices[0];
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * this->pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);
        
        glPointSize(10.0f);
        
        glDrawArrays(GL_POINTS, 0, this->solver->pos.size()+1);

        ui::check_for_opengl_errors();
    }
};