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

set_property(GLOBAL PROPERTY CXX_STANDARD 11)
set_property(GLOBAL PROPERTY CXX_STANDARD_REQUIRED ON)

string(TIMESTAMP CMAKE_BUILD_TIMESTAMP "%H:%M:%S %m-%d-%Y")
message("-- Timestamp: ${CMAKE_BUILD_TIMESTAMP}")

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/arch)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Detect Linux
if(UNIX AND NOT APPLE)
    set(LINUX TRUE)
    add_definitions(-DLINUX=1)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
endif()

# Detect MinGW
if (MINGW)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wa,-mbig-obj")
endif()

# Detect Apple
if (APPLE)
    # Startlingly, this flag isn't set automatically, so here it is.
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
    set(CMAKE_OSX_DEPLOYMENT_TARGET 10.10)
    set(CMAKE_OSX_ARCHITECTURES x86_64 )
endif (APPLE)

# Set up some useful messages and defines based on build type
if (CMAKE_BUILD_TYPE EQUAL "Release")
    message("-- Building Release")
    add_definitions(-DNDEBUG=1)
    add_definitions(-D_NDEBUG=1)
else()
    message("-- Building Debug")
    add_definitions(-D_DEBUG)
    add_definitions(-DDEBUG)
endif()

