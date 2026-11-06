cmake_minimum_required(VERSION 3.26...3.31)
project(compas_shapeop LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(COMPAS_SHAPEOP_OPENMP "Enable ShapeOp OpenMP support" OFF)

include(FetchContent)
FetchContent_Declare(
  eigen
  URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
  URL_HASH SHA256=8586084f71f9bde545ee7fa6d00288b264a2b7ac3607b974e54d13e7162c1c72
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
  # Eigen is header-only here. Populate its sources without adding its CMake
  # project, whose install rules would otherwise copy the entire source tree
  # into the Python wheel.
  SOURCE_SUBDIR _compas_shapeop_header_only
)
FetchContent_MakeAvailable(eigen)

find_package(Python 3.12 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

if(COMPAS_SHAPEOP_OPENMP)
  find_package(OpenMP REQUIRED COMPONENTS CXX)
endif()

add_library(shapeop STATIC
  src/shapeop/Constraint.cpp
  src/shapeop/Force.cpp
  src/shapeop/LSSolver.cpp
  src/shapeop/Solver.cpp
  src/shapeop/custom_constraints/NormalForce.cpp
)
set_target_properties(shapeop PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_compile_features(shapeop PUBLIC cxx_std_20)
target_compile_definitions(shapeop PUBLIC SHAPEOP_EXPORT)
target_include_directories(shapeop PUBLIC src ${eigen_SOURCE_DIR})
target_link_libraries(shapeop PUBLIC Threads::Threads)

if(COMPAS_SHAPEOP_OPENMP)
  target_compile_definitions(shapeop PUBLIC SHAPEOP_OPENMP)
  target_link_libraries(shapeop PUBLIC OpenMP::OpenMP_CXX)
endif()

nanobind_add_module(_shapeop STABLE_ABI NB_STATIC src/shapeop.cpp)
target_compile_features(_shapeop PRIVATE cxx_std_20)
target_include_directories(_shapeop PRIVATE src ${eigen_SOURCE_DIR})
target_link_libraries(_shapeop PRIVATE shapeop Threads::Threads)
if(COMPAS_SHAPEOP_OPENMP)
  target_link_libraries(_shapeop PRIVATE OpenMP::OpenMP_CXX)
endif()

install(TARGETS _shapeop LIBRARY DESTINATION compas_shapeop RUNTIME DESTINATION compas_shapeop)
