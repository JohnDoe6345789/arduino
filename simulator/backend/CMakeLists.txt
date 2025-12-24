cmake_minimum_required(VERSION 3.21)
project(arduino_simulator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(fmt REQUIRED)

add_library(sim_core
    src/board.cpp
)

target_include_directories(sim_core PUBLIC include)
target_link_libraries(sim_core PUBLIC fmt::fmt)

add_executable(sim_driver
    src/main.cpp
)

target_link_libraries(sim_driver PRIVATE sim_core fmt::fmt)

enable_testing()

add_executable(sim_core_smoke_tests tests/smoke.cpp)
target_link_libraries(sim_core_smoke_tests PRIVATE sim_core fmt::fmt)
add_test(NAME sim_core_smoke COMMAND sim_core_smoke_tests)
