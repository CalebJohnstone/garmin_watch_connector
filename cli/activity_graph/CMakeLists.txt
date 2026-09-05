cmake_minimum_required(VERSION 3.20)
project(activity_graph LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(libpqxx REQUIRED)
find_package(ftxui CONFIG REQUIRED)
find_package(CLI11 CONFIG REQUIRED)

add_executable(activity_graph
    src/main.cpp
    src/env_config.cpp
    src/db.cpp
    src/charts.cpp
)

target_link_libraries(activity_graph PRIVATE
    libpqxx::pqxx
    ftxui::ftxui
    CLI11::CLI11
)
