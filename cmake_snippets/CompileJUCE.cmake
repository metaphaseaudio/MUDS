#
# CompileJUCE.cmake
#   Matt Zapp - 2018
#
#   This snippet can be used to include JUCE as a statically-linked library in
#   your project.  To use, follow these steps:
#
#   1. Create two header files in the same directory, `AppConfig.h` and
#      `JuceHeader.h`.  These files should follow the format of the files
#      normally generated by the JUCE Projucer, or be directly generated by the
#      Projucer.
#   2. Add an `include_directories` directive that points to the directory
#      containing these files.
#   3. Add: `set(JUCE_APP_CONFIG <path_to_config>/AppConfig.h)` to your
#      top-level `CMakeLists.txt` file.
#   4. Set variables corresponding to each of the modules relevant to your
#      project in the format `JUCE_ENABLE_<MODULE_NAME>`.  Examples:
#           Enable the Audio Basics module: `set(JUCE_ENABLE_AUDIO_BASICS ON)`
#           Enable the VST Plug-in build: `set(JUCE_ENABLE_PLUGIN_VST ON)`
#
#   5. Add: `set(JUCE_PATH <path_to_juce_root_folder>)`
#   6. Include this snippet
#
#   Later in your project you will be able use the following variables:
#       -- JUCE_SOURCE: the source files required to build JUCE
#       -- JUCE_LIBS: the libraries need by this platform
#       -- JUCE_PLUGIN_SOURCE: For building plugins if needed
#
#   To link, add `juce` to your project's `target_link_libraries` directive.
#

include_directories(${JUCE_PATH}/modules)
add_definitions(-DJUCE_APP_CONFIG_HEADER="${JUCE_APP_CONFIG}")

# You may uncomment any of these lines only if you have paid for JUCE.
#add_definitions(-DJUCE_DISABLE_JUCE_VERSION_PRINTING=1)
#add_definitions(-DJUCE_DISPLAY_SPLASH_SCREEN=0)
#add_definitions(-DJUCE_REPORT_APP_USAGE=0)

# OS X requires an alternate, Objective-C file extension for some modules, but
# most compilers do not need anything more than the basic cpp extension.
set(FILE_FORMAT ".cpp")
#   TODO: Move platform-specific library requirements to each module.
#------------------------------------------------------------------------------
# Apple-Specific libraries
#------------------------------------------------------------------------------
if(APPLE)
    add_definitions(-DJUCE_MAC=1)
    set(FILE_FORMAT ".mm")
    find_library(ACCELERATE_LIBRARY Accelerate)
    find_library(AUDIOTOOLBOX_LIBRARY AudioToolbox)
    find_library(AUDIOUNIT_LIBRARY AudioUnit)
    find_library(CARBON_LIBRARY Carbon)
    find_library(COCOA_LIBRARY Cocoa)
    find_library(COREAUDIO_LIBRARY CoreAudio)
    find_library(COREMIDI_LIBRARY CoreMIDI)
    find_library(DISCRECORDING_LIBRARY DiscRecording)
    find_library(IOKIT_LIBRARY IOKit)
    find_library(OPENGL_LIBRARY OpenGL)
    find_library(QTKIT_LIBRARY QTKit)
    find_library(QUARTZCORE_LIBRARY QuartzCore)
    find_library(WEBKIT_LIBRARY WebKit)

    mark_as_advanced(ACCELERATE_LIBRARY
                     AUDIOTOOLBOX_LIBRARY
                     AUDIOUNIT_LIBRARY
                     CARBON_LIBRARY
                     COCOA_LIBRARY
                     COREAUDIO_LIBRARY
                     COREMIDI_LIBRARY
                     DISCRECORDING_LIBRARY
                     IOKIT_LIBRARY
                     OPENGL_LIBRARY
                     QTKIT_LIBRARY
                     QUARTZCORE_LIBRARY
                     QUICKTIME_LIBRARY
                     WEBKIT_LIBRARY)

   set(JUCE_LIBS
     ${ACCELERATE_LIBRARY}
     ${AUDIOTOOLBOX_LIBRARY}
     ${AUDIOUNIT_LIBRARY}
     ${CARBON_LIBRARY}
     ${COCOA_LIBRARY}
     ${COREAUDIO_LIBRARY}
     ${COREMIDI_LIBRARY}
     ${DISCRECORDING_LIBRARY}
     ${IOKIT_LIBRARY}
     ${OPENGL_LIBRARY}
     ${QTKIT_LIBRARY}
     ${QUARTZCORE_LIBRARY}
     ${QUICKTIME_LIBRARY}
     ${WEBKIT_LIBRARY})
endif(APPLE)

#------------------------------------------------------------------------------
# Linux-Specific libraries
#------------------------------------------------------------------------------
if (LINUX)
    add_definitions(-DJUCE_LINUX=1)
    if (JUCE_JACK)
        add_definitions(-DJUCE_JACK=1)
    endif (JUCE_JACK)

    if (JUCE_ALSA)
        add_definitions(-DJUCE_ALSA=1)
    endif(JUCE_ALSA)

    find_library(DL       dl)
    find_package(Threads  REQUIRED)
    find_package(Freetype REQUIRED)
    find_package(ALSA     REQUIRED)
    find_package(X11      REQUIRED)
    find_library(RT       rt)

    set(JUCE_LIBS
        ${ALSA_LIBRARIES}
        ${CMAKE_THREAD_LIBS_INIT}
        ${DL}
        ${OPENGL_LIBRARIES}
        ${FREETYPE_LIBRARIES}
        ${RT}
        ${X11_LIBRARIES})

    include_directories(AFTER ${FREETYPE_INCLUDE_DIRS})
endif (LINUX)

#------------------------------------------------------------------------------
# Windows-Specific libraries
#------------------------------------------------------------------------------
if (WIN32)
    add_definitions(-DJUCE_WINDOWS=1)

    # MSVC seems to handle itself admirably, however,
    # MinGW requires a little hand-holding
    if (MINGW)
        add_definitions("-DJUCE_MINGW")
        find_library(IMM32 imm32 REQUIRED)
        find_library(COMDLG32 comdlg32 REQUIRED)
        find_library(LIBVERSION version REQUIRED)
        find_library(OLE32 ole32 REQUIRED)
        find_library(OLEAUT32 oleaut32 REQUIRED)
        find_library(RPCRT4 rpcrt4 REQUIRED)
        find_library(SHLWAPI shlwapi REQUIRED)
        find_library(WS2_32 ws2_32 REQUIRED)
        find_library(WSOCK32 wsock32 REQUIRED)
        find_library(WININET wininet REQUIRED)
        find_library(WINMM winmm REQUIRED)
        set (JUCE_LIBS
                ${COMDLG32}
                ${IMM32}
                ${LIBVERSION}
                ${OLE32}
                ${OLEAUT32}
                ${RPCRT4}
                ${SHLWAPI}
                ${WSOCK32}
                ${WININET}
                ${WINMM}
                ${WS2_32})
	else()
        add_definitions("-DJUCE_MSVC")
    endif()

endif (WIN32)

#------------------------------------------------------------------------------
# Boilerplate code collection and defines
#------------------------------------------------------------------------------
if (CMAKE_BUILD_TYPE EQUAL "Debug")
    add_definitions(-DJUCE_DEBUG)
endif()

message("-- JUCE: using Core module")
set(JUCE_SOURCE ${JUCE_PATH}/modules/juce_core/juce_core${FILE_FORMAT})

#------------------------------------------------------------------------------
# Plug-in enablement
#------------------------------------------------------------------------------
set(JUCE_PLUGIN_SOURCE)
if (JUCE_ENABLE_PLUGIN_VST)
    message("-- JUCE: building VST Plug-in")

    list(APPEND JUCE_PLUGIN_SOURCE
            ${JUCE_PATH}/modules/juce_audio_plugin_client/VST/juce_VST_Wrapper${FILE_FORMAT}
            ${JUCE_PATH}/modules/juce_audio_plugin_client/VST/juce_VST_Wrapper.cpp
            ${JUCE_PATH}/modules/juce_audio_plugin_client/utility/juce_PluginUtilities.cpp)

    add_definitions(-DJucePlugin_Build_VST=1)
elseif (JUCE_ENABLE_PLUGIN_VST)
    add_definitions(-DJucePlugin_Build_VST=0)
endif (JUCE_ENABLE_PLUGIN_VST)

if (JUCE_ENABLE_PLUGIN_AU)
    add_definitions(-DJucePlugin_Build_AU=1)
elseif (JUCE_ENABLE_PLUGIN_AU)
    add_definitions(-DJucePlugin_Build_AU=0)
endif (JUCE_ENABLE_PLUGIN_AU)

if (JUCE_ENABLE_PLUGIN_LV2)
    add_definitions(-DJucePlugin_Build_LV2=1)
elseif (JUCE_ENABLE_PLUGIN_LV2)
    add_definitions(-DJucePlugin_Build_LV2=0)
endif (JUCE_ENABLE_PLUGIN_LV2)

#------------------------------------------------------------------------------
# Module enablement
#------------------------------------------------------------------------------
if (JUCE_ENABLE_AUDIO_BASICS)
    message("-- JUCE: using Audio Basics module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_audio_basics/juce_audio_basics${FILE_FORMAT})
endif()

if (JUCE_ENABLE_AUDIO_FORMATS)
    message("-- JUCE: using Audio Formats module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_audio_formats/juce_audio_formats${FILE_FORMAT})
endif()

if (JUCE_ENABLE_AUDIO_DEVICES)
    message("-- JUCE: using Audio Devices module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_audio_devices/juce_audio_devices${FILE_FORMAT})
endif()

if (JUCE_ENABLE_AUDIO_PROCESSORS)
    message("-- JUCE: using Audio Processors module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_audio_processors/juce_audio_processors${FILE_FORMAT})
endif()

if (JUCE_ENABLE_AUDIO_UTILS)
    message("-- JUCE: using Audio Utils module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_audio_utils/juce_audio_utils${FILE_FORMAT})
endif()

if (JUCE_ENABLE_BOX_2D)
    message("-- JUCE: using Box 2D module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_box2d/juce_box2d${FILE_FORMAT})
endif()

if (JUCE_ENABLE_BROWSER_PLUGIN)
    message("-- JUCE: using Browser Plugin module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_browser_plugin_client/juce_browser_plugin${FILE_FORMAT})
endif()

if (JUCE_ENABLE_CRYPTOGRAPHY)
    message("-- JUCE: using Cryptography module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_cryptography/juce_cryptography${FILE_FORMAT})
endif()

if (JUCE_ENABLE_DSP)
    message("-- JUCE: using DSP module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_dsp/juce_dsp${FILE_FORMAT})
    add_definitions(-DJUCE_MODULE_AVAILABLE_juce_dsp=1)
endif()

if (JUCE_ENABLE_DATA_STRUCTURES)
    message("-- JUCE: using Data Structures module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_data_structures/juce_data_structures${FILE_FORMAT})
endif()

if (JUCE_ENABLE_EVENTS)
    message("-- JUCE: using Events module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_events/juce_events${FILE_FORMAT})
endif()

if (JUCE_ENABLE_GRAPHICS)
    message("-- JUCE: using Graphics module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_graphics/juce_graphics${FILE_FORMAT})
endif()

if (JUCE_ENABLE_GUI_BASICS)
    message("-- JUCE: using GUI Basics module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_gui_basics/juce_gui_basics${FILE_FORMAT})
endif()

if (JUCE_ENABLE_GUI_EXTRA)
    message("-- JUCE: using GUI Extra module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_gui_extra/juce_gui_extra${FILE_FORMAT})
endif()

if (JUCE_ENABLE_OPENGL)
    message("-- JUCE: using OpenGL module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_opengl/juce_opengl${FILE_FORMAT})
endif()

if (JUCE_ENABLE_OSC)
    message("-- JUCE: using OSC module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_osc/juce_osc.cpp)
endif()

if (JUCE_ENABLE_VIDEO)
    message("-- JUCE: using Video module")
    set(JUCE_SOURCE ${JUCE_SOURCE} ${JUCE_PATH}/modules/juce_video/juce_video${FILE_FORMAT})
endif()

#------------------------------------------------------------------------------
# Compilation
#------------------------------------------------------------------------------
add_library(juce STATIC ${JUCE_SOURCE})
set_property(TARGET juce PROPERTY POSITION_INDEPENDENT_CODE ON)
target_link_libraries(juce ${JUCE_LIBS})

if(THREADS_HAVE_PTHREAD_ARG)
    set_property(TARGET juce PROPERTY COMPILE_OPTIONS "-pthread")
    set_property(TARGET juce PROPERTY INTERFACE_COMPILE_OPTIONS "-pthread")
endif()
