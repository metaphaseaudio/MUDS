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
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    message("-- Building Debug")
    add_definitions(-DDEBUG=1)
    add_definitions(-D_DEBUG=1)
else()
    message("-- Building Release")
    add_definitions(-DNDEBUG=1)
    add_definitions(-D_NDEBUG=1)
endif()

option(BUILD_TESTS OFF)

if (BUILD_TESTS)
    configure_file(${MUDS_ROOT}/cmake_snippets/gtest/CMakeLists.txt.in googletest-download/CMakeLists.txt)
    execute_process(COMMAND ${CMAKE_COMMAND} -G "${CMAKE_GENERATOR}" .
            RESULT_VARIABLE result
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/googletest-download )
    if(result)
        message(FATAL_ERROR "CMake step for googletest failed: ${result}")
    endif()
    execute_process(COMMAND ${CMAKE_COMMAND} --build .
            RESULT_VARIABLE result
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/googletest-download )
    if(result)
        message(FATAL_ERROR "Build step for googletest failed: ${result}")
    endif()

    # Prevent overriding the parent project's compiler/linker
    # settings on Windows
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

    # Add googletest directly to our build. This defines
    # the gtest and gtest_main targets.
    add_subdirectory(${CMAKE_BINARY_DIR}/googletest-src
            ${CMAKE_BINARY_DIR}/googletest-build
            EXCLUDE_FROM_ALL)

    include_directories("${gtest_SOURCE_DIR}/include")
        
	set(GTEST_LIBRARIES gtest gtest_main)
	enable_testing()
	add_definitions(-DMETA_BUILD_TESTS=1)
endif()