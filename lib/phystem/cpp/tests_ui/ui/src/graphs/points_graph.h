#pragma once

#include <array>
#include <vector>
#include "../core_graphs.h"

namespace ui {
namespace graphs {

template<class Solver, class GraphCfg> 
class PointsGraph : public CoreMainGraph<Solver, GraphCfg> {
public:
    using CoreMainGraph<Solver, GraphCfg>::CoreMainGraph;

private:
    void setup_main() override {
        auto item = CoreMainGraph<Solver, GraphCfg>::RenderItem::Main;

        this->shaders[item] = Shader((shader_dir + "points/vertex.glsl").c_str(), (shader_dir + "points/fragment.glsl").c_str()); 
        auto& shader = this->shaders[item];

        this->scene_obj[item] = SceneObjetcs();
        auto& obj = this->scene_obj[item]; 

        glGenVertexArrays(1, &obj.VAO);
        glGenBuffers(1, &obj.VBO);

        glBindVertexArray(obj.VAO);

        glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);

        this->pos_vertices = std::vector<float>(this->solver->pos.size()*2, 0.0);
        float* vertices = &this->pos_vertices[0];
        
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * this->pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void *)0);
        glEnableVertexAttribArray(0);

        ui::check_for_opengl_errors();
    }

    virtual void transform(std::array<double, 2>& pos) = 0;
    // Transforma a coordenada dada para o espaço da renderização.

    void update_vertices() override {
        for (size_t i = 0; i < this->solver->pos.size(); i++)
        {
            auto pos_i = this->solver->pos[i];
            transform(pos_i);
            
            // pos_i[0] /= solver->get_size() * 0.5;
            // pos_i[1] /= solver->get_size() * 0.5;

            this->pos_vertices[2*i] = pos_i[0];
            this->pos_vertices[2*i + 1] = pos_i[1];
        }
    }

    void update_main() override {
        auto item = CoreMainGraph<Solver, GraphCfg>::RenderItem::Main;

        update_vertices();

        this->shaders[item].use();        
        
        this->shaders[item].setFloat3("color", this->graph_cfg.color);
        
        glBindVertexArray(this->scene_obj[item].VAO);
        
        glBindBuffer(GL_ARRAY_BUFFER, this->scene_obj[item].VBO);
        float* vertices = &this->pos_vertices[0];
        glBufferData(GL_ARRAY_BUFFER, sizeof(float) * this->pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);
        
        glPointSize(10.0f);
        
        glDrawArrays(GL_POINTS, 0, this->solver->pos.size());

        // check_for_opengl_errors();
    }
};


} // namespace graph
} // namespace ui
