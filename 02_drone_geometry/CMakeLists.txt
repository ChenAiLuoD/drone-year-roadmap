# 要求最低使用 CMake 3.22。
cmake_minimum_required(VERSION 3.22)

# 声明最终作品项目名称，并启用 C++。
project(drone_geometry LANGUAGES CXX)

# 统一使用 C++17，避免编译器使用旧标准解释代码。
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Eigen 主要提供头文件，不需要单独链接运行时库。
find_package(Eigen3 3.3 REQUIRED NO_MODULE)

# 启用 CTest，后面用 ctest 运行 GoogleTest。
include(CTest)

# 核心库负责 CSV 读写和 T_target_source 坐标变换。
add_library(drone_geometry_core
    src/trajectory_transform.cpp
)

# 把项目头文件目录作为库的公开使用要求传递出去。
target_include_directories(drone_geometry_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# 把 Eigen 的头文件路径传给核心库及其使用者。
target_link_libraries(drone_geometry_core
    PUBLIC
        Eigen3::Eigen
)

# 命令行程序负责解析参数、调用核心库并输出日志。
add_executable(transform_trajectory
    src/cli.cpp
    src/main.cpp
)

# 主程序链接核心库。
target_link_libraries(transform_trajectory
    PRIVATE
        drone_geometry_core
)

# 在目标级别启用常用警告，避免污染其他依赖。
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(drone_geometry_core PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
    target_compile_options(transform_trajectory PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

# 使用 GoogleTest 验证旋转、平移和距离保持性质。
if(BUILD_TESTING)
    find_package(GTest REQUIRED)

    add_executable(drone_geometry_tests
        tests/trajectory_transform_test.cpp
    )

    target_link_libraries(drone_geometry_tests
        PRIVATE
            drone_geometry_core
            GTest::gtest_main
    )

    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(drone_geometry_tests PRIVATE
            -Wall
            -Wextra
            -Wpedantic
        )
    endif()

    include(GoogleTest)
    gtest_discover_tests(drone_geometry_tests)
endif()
