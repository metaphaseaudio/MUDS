# MUDS: -- Metaphase Useful Development Scripts
Building C/C++ applications can be a complicated business, so it is common to
establish as repeatable a project structure as possible.  This has the benefits
of reducing the mental taxation of context-switching when moving between
projects, and allowing boilerplate build code to be used for every project with
minimal tweaks.

This repository provides build scripts and CMake snippets that are used in
nearly every Metaphase project with the hope that they will be useful in other
projects as well. Most scripts here will primarily be useful to projects using
CMake, or the [JUCE](https://github.com/WeAreROLI/JUCE) library.

This is not a stand-alone product, nor a finished one (if that's ever possible
with build systems,) but rather a repository in which the Metaphase project
structure and coding standards can be codified and supported.

### The Standard Metaphase Project Layout:
```
  -- /<project_name>
    -- /build                      // **Auto-generated by build scripts**
      -- /bin                      // Executables are output here
      -- /lib                      // Libraries are output here
      -- /arch                     // Object archive files are output here
    -- /src
      -- CMakeLists.txt            // Top-Level Project CMakeLists file
      -- /<project_specific_code>
        -- inc                     // Project header files
        -- src                     // Project source files
      -- /juce_includes            // Optional unless working with JUCE.
        -- AppConfig.h             // See `CompileJUCE.cmake` for details
        -- JuceHeader.h            // See `CompileJUCE.cmake` for details
      -- /shared                   // All optional shared code goes here
        -- /JUCE
        -- /<submodule>
        -- /<submodule>
      -- /test                     // Optionally compiled Google Test directory
         -- AllTests.cpp           // Includes all the test `.h` files and runs Google Test
         -- CMakeLists.txt         // Test compilation script
         -- /tests                 // Tests go here
           -- <test_ObjectUnderTest.h>
    -- /scripts
      -- build_debug.sh            // Deletes the build folder and builds DEBUG
      -- build_release.sh          // Deletes the build folder and builds RELEASE
      -- rebuild_debug.sh          // Builds DEBUG
      -- rebuild_release.sh        // Builds RELEASE
```

### Constructing a Metaphase Project
  - The project's top-level `CMakeLists.txt` file includes a MUDS boilerplate CMake
helper file to set up all the general paths and variables to be used in all
subdirectories' CMakeLists.txt files.

  - Next, to include shared code, this top-level file will then either use
`add_subdirectory` or one of the MUDS CMake snippets to build it. What a
suproject looks like can be very flexible, but each subdirectory in the shared
code folder tends to relate 1-to-1 with a static library in most Metaphase
projects.

  - To complete the CMake-base portion of a project, the top-level CMakeLists.txt
will finally GLOB together all the source and header files found in the
`<project_specific_code>` folder, declare the project's output target using the
GLOBed source, and link any shared libraries made in the previous step.

  - If this project will be built either in an automated system or from the command
line, a few build scripts can be handy to help reduce the challenge of getting
a bunch of specific CMake calls right by hand every single time.  Most
Metaphase projects use the four standard scripts listed earlier, but others
that enable unit test builds, or specify different build configurations may be
needed.

  - Each of the listed scripts calls to one of two boilerplate build scripts in the
MUDS repository that either deletes the build folder or not before refreshing
the CMake Cache and kicking off a build. The variations automatically pass the
build-type argument to the boilerplate scripts and allow for any additional
arguments to be passed from the command line.

### Building a Metaphase Project
From the root directory, run one of the build scripts from the `scripts`
folder.  Output will be placed in the `build`, if a MUDS boilerplate CMake
snippet is used, the bin and lib subdirectories will contain the built
executables and libraries respectively.

### Thanks:
Thanks are due to Matthias Kronlachner for providing excellent examples of how
CMake scripts can be used to build cross-platform JUCE projects without the use
of the Projucer: https://github.com/kronihias.
