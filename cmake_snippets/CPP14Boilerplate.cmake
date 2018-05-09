#
# CPP11Boilerplate.cmake
#   Matt Zapp - 2018
#
#   There are a lot of generic boilerplate CMake directives required to
#   generate modern C++ code.  This particular snippet handles the required
#   directives to generate compiler flags that support C++11 specifically on
#   most platforms, but with a few tweaks it could be made to support any other
#   specific modern C++ standard.
#
#   To use, simply add include this snippet *after* your top-level
#   CMakeLists.txt project declaration.
#
set(MUDS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/shared/MUDS/)
set_property(GLOBAL PROPERTY CXX_STANDARD 14)
set_property(GLOBAL PROPERTY CXX_STANDARD_REQUIRED ON)

if(UNIX AND NOT APPLE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")
endif()

include(${MUDS_ROOT}/cmake_snippets/CPPGeneralBoilerplate.cmake)


