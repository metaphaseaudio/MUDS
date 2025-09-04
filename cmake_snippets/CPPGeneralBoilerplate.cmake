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
message("<< MUDS Build System v0.1 >>")
set(MUDS_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/shared/MUDS/)

string(TIMESTAMP CMAKE_BUILD_TIMESTAMP "%H:%M:%S %m-%d-%Y")
message("-- Timestamp: ${CMAKE_BUILD_TIMESTAMP}")
message("-- Compiler ID: ${CMAKE_CXX_COMPILER_ID}")

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/arch)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)


# Add modules
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${MUDS_ROOT}/cmake_modules/")

# Detect Linux
if(UNIX AND NOT APPLE)
    set(LINUX TRUE)
    add_definitions(-DLINUX=1)
endif()

# Detect MinGW
if (MINGW)
	message("-- MinGW detected")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wa,-mbig-obj")
endif()

# Detect MSVC
if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
	message("-- MSVC detected")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /constexpr:steps2147483647")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /constexpr:depth1024")
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -msse3") 
	message("-- Clang detected")
    set(CLANG TRUE)
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
    # This block is googletest's recommended way of including gtest.
    include(FetchContent)
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/refs/tags/v1.17.0.zip
    )

    # For Windows: Prevent overriding the parent project's compiler/linker settings
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    # This block sets some helpers and enables testing.
	enable_testing()
    set(GTEST_LIBRARIES GTest::gtest_main)
    include(GoogleTest)
    add_definitions(-DMETA_BUILD_TESTS=1)
endif()
