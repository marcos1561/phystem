#include <cstdio>
#include <GLFW/glfw3.h>

namespace ui
{
    
bool check_for_opengl_errors() {
    char errNames[9][36] = {
        "Unknown OpenGL error",
        "GL_INVALID_ENUM", "GL_INVALID_VALUE", "GL_INVALID_OPERATION",
        "GL_INVALID_FRAMEBUFFER_OPERATION", "GL_OUT_OF_MEMORY",
        "GL_STACK_UNDERFLOW", "GL_STACK_OVERFLOW", "GL_CONTEXT_LOST" };

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

} // namespace ui