#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <cmath>
#include <map>

#include "headers/main_graph.h"

bool check_for_opengl_errors();

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

MainGraph::MainGraph(SelfPropelling* in_solver, ElementGeometry el_geo, GLFWwindow* window) {
    solver = in_solver;
    pos_vertices = std::vector<float>(2*solver->pos.size());

    graph_cfg.color[0] = 1.0f;
    graph_cfg.color[1] = 1.0f;
    graph_cfg.color[2] = 0.0f;

    graph_cfg.speed = 1;
    graph_cfg.is_paused = false;

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

void MainGraph::update_pos_vertices() {
    for (size_t i = 0; i < solver->pos.size(); i++)
    {
        auto pos_i = solver->pos[i];
        
        pos_i[0] /= solver->get_size() * 0.5;
        pos_i[1] /= solver->get_size() * 0.5;

        pos_vertices[2*i] = pos_i[0];
        pos_vertices[2*i + 1] = pos_i[1];
    }
    
}

void MainGraph::setup_main() {
    auto item = RenderItem::Main;

    shaders[item] = Shader("../src/shaders/points/vertex.glsl", "../src/shaders/points/fragment.glsl"); 
    auto& shader = shaders[item];

    scene_obj[item] = SceneObjetcs();
    auto& obj = scene_obj[item]; 

    glGenVertexArrays(1, &obj.VAO);
    glGenBuffers(1, &obj.VBO);

    glBindVertexArray(obj.VAO);

    glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);

    float* vertices = &pos_vertices[0];
    
    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * pos_vertices.size(), vertices, GL_DYNAMIC_DRAW);

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void *)0);
    glEnableVertexAttribArray(0);

    check_for_opengl_errors();
}

void MainGraph::update_main() {
    auto item = RenderItem::Main;

    update_pos_vertices();

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

void MainGraph::setup_triangle() {
    shaders[RenderItem::Triangle] = Shader("../src/shaders/vertex.glsl", "../src/shaders/fragment.glsl");
    
    // Vertex data
    float vertices[] = {
    // positions         // colors
     0.5f, 0.5f, 0.0f,  1.0f, 0.0f, 0.0f,   // bottom right
    -0.5f, 0.5f, 0.0f,  0.0f, 1.0f, 0.0f,   // bottom left
     0.0f, -0.5f, 0.0f,  0.0f, 0.0f, 1.0f    // top 
    }; 

    unsigned int indices[] = {  // note that we start from 0!
        0, 1, 3,  // first Triangle
        1, 2, 3   // second Triangle
    };

    scene_obj[RenderItem::Triangle] = SceneObjetcs();
    auto& obj = scene_obj[RenderItem::Triangle];

    // Vertex configuration
    glGenVertexArrays(1, &obj.VAO);
    glGenBuffers(1, &obj.VBO);

    glBindVertexArray(obj.VAO);

    glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);   
    
    check_for_opengl_errors();
}

void MainGraph::setup_points() {
    shaders[RenderItem::Points] = Shader("../src/shaders/points/vertex.glsl", "../src/shaders/points/fragment.glsl");
    
    // Vertex data
    float vertices[] = {
		1.0f, 1.0f,  // First point
		1.0f, -1.0f,   // Second point
		-1.0f, 1.0f,	   // Third point
		-1.0f, -1.0f,	   // Third point
		0.0f, 0.0f,	   // Third point
	};

    scene_obj[RenderItem::Points] = SceneObjetcs();
    auto& obj = scene_obj[RenderItem::Points];

    // Vertex configuration
    glGenVertexArrays(1, &obj.VAO);
    glGenBuffers(1, &obj.VBO);

    glBindVertexArray(obj.VAO);

    glBindBuffer(GL_ARRAY_BUFFER, obj.VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    check_for_opengl_errors();
}

void MainGraph::setup_boarder() {
    shaders[RenderItem::Border] = Shader("../src/shaders/points/vertex.glsl", "../src/shaders/points/fragment.glsl");
    
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

    check_for_opengl_errors();
}

void MainGraph::setup_background() {
    auto item = RenderItem::Background;

    shaders[item] = Shader("../src/shaders/points/vertex.glsl", "../src/shaders/points/fragment.glsl");
    auto& shader = shaders[item];

    // Vertex data
    float vertices[] = {
		-1.0f, 1.0f, 
        1.0f, 1.0f,  
		-1.0f, -1.0f, 
        1.0f, 1.0f,   
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

    check_for_opengl_errors();
}

void MainGraph::update_points() {
    auto item = RenderItem::Points;

    shaders[item].use();        
    
    shaders[item].setFloat3("color", graph_cfg.color);
    glPointSize(40.0f);
    glBindVertexArray(scene_obj[item].VAO);
    glDrawArrays(GL_POINTS, 0, 5);
}

void MainGraph::update_boarder() {
    auto item = RenderItem::Border;

    shaders[item].use();        
    
    // shaders[item].setFloat3("color", graph_cfg.color);
    glLineWidth(40.0f);
    glBindVertexArray(scene_obj[item].VAO);
    glDrawArrays(GL_LINES, 0, 16);
}

void MainGraph::update_background() {
    auto item = RenderItem::Background;

    shaders[item].use();        
    
    // shaders[item].setFloat3("color", graph_cfg.color);
    glBindVertexArray(scene_obj[item].VAO);
    glDrawArrays(GL_TRIANGLES, 0, 6);
}

void MainGraph::update_triangle() {
    auto mode = RenderItem::Triangle;

    shaders[mode].use();
        
    float time = glfwGetTime();
    float offset = (sin(time) / 2.0f);
    shaders[mode].setFloat("offset", offset);

    glBindVertexArray(scene_obj[mode].VAO);
    glDrawArrays(GL_TRIANGLES, 0, 3);
}

void MainGraph::setup() {
    setup_boarder();
    setup_main();
    // setup_triangle();
    // setup_points();
    setup_background();
}

void MainGraph::update() {
    update_background();
    update_main();
    // update_points();
    // update_triangle();
    update_boarder();
}

char errNames[9][36] = {
    "Unknown OpenGL error",
    "GL_INVALID_ENUM", "GL_INVALID_VALUE", "GL_INVALID_OPERATION",
    "GL_INVALID_FRAMEBUFFER_OPERATION", "GL_OUT_OF_MEMORY",
    "GL_STACK_UNDERFLOW", "GL_STACK_OVERFLOW", "GL_CONTEXT_LOST" };
bool check_for_opengl_errors() {
    int numErrors = 0;
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        numErrors++;
        int errNum = 0;
        switch (err) {
        case GL_INVALID_ENUM:
            errNum = 1;
            break;
        case GL_INVALID_VALUE:
            errNum = 2;
            break;
        case GL_INVALID_OPERATION:
            errNum = 3;
            break;
        case GL_INVALID_FRAMEBUFFER_OPERATION:
            errNum = 4;
            break;
        case GL_OUT_OF_MEMORY:
            errNum = 5;
            break;
        // case GL_STACK_UNDERFLOW:
        //     errNum = 6;
        //     break;
        // case GL_STACK_OVERFLOW:
        //     errNum = 7;
        //     break;
        // case GL_CONTEXT_LOST:
        //     errNum = 8;
        //     break;
        }
        printf("OpenGL ERROR: %s.\n", errNames[errNum]);
    }
    return (numErrors != 0);
}
