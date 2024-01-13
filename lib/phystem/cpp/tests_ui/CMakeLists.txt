cmake_minimum_required(VERSION 3.10)

project(Tests VERSION 1.0)

# set(CMAKE_BUILD_TYPE "Debug")

include_directories(${PROJECT_SOURCE_DIR})
include_directories(ui/deps/glad/include)
include_directories(ui/deps/imgui/include)

add_subdirectory(ui)

add_executable(main self_propelling/main.cpp)
# add_executable(main rigid_potencial/main.cpp rigid_potencial/solver.cpp)
# add_executable(main area_potencial/main.cpp area_potencial/solver.cpp)

target_link_libraries(main app_deps)