cmake_minimum_required(VERSION 3.10)

project(UiCore VERSION 1.0)

include_directories(deps/glad/include)
include_directories(deps/imgui/include)

file(GLOB IMGUI_SRC ${PROJECT_SOURCE_DIR}/deps/imgui/src/*.cpp)

add_library(app_deps src/timer.cpp src/opengl_error.cpp ${IMGUI_SRC})

add_library(glad deps/glad/src/glad.c)
target_link_libraries(app_deps glad)

set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)

add_subdirectory(deps/glfw-3.3.8)
target_link_libraries(app_deps glfw)

find_package(OpenGL REQUIRED)
target_link_libraries(app_deps OpenGL::GL)
