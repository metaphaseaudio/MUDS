# OpenSSL-Static.cmake
# Builds OpenSSL from source as static libraries and provides imported targets
# Supports universal binaries on macOS
#
# Usage:
#   include(cmake/OpenSSL-Static.cmake)
#   target_link_libraries(your_target PRIVATE OpenSSL::SSL OpenSSL::Crypto)
#
# Provides:
#   OpenSSL::SSL - Static SSL library
#   OpenSSL::Crypto - Static Crypto library
#
# Variables:
#   OPENSSL_VERSION - Version to build (default: 3.2.0)
#   OPENSSL_INSTALL_DIR - Installation directory (default: ${CMAKE_BINARY_DIR}/deps/openssl)

cmake_minimum_required(VERSION 3.20)

# Allow version override
if(NOT DEFINED OPENSSL_VERSION)
    set(OPENSSL_VERSION "3.2.0")
endif()

# Installation directory
if(NOT DEFINED OPENSSL_INSTALL_DIR)
    set(OPENSSL_INSTALL_DIR ${CMAKE_BINARY_DIR}/deps/openssl)
endif()

include(ExternalProject)

set(OPENSSL_URL "https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz")

# ============================================================================
# Platform-Specific Configuration
# ============================================================================
if(WIN32)
    # Windows requires Perl and NASM
    set(OPENSSL_CONFIGURE_COMMAND
            perl Configure VC-WIN64A no-shared no-tests
            --prefix=${OPENSSL_INSTALL_DIR}
            --openssldir=${OPENSSL_INSTALL_DIR}
    )
    set(OPENSSL_BUILD_COMMAND nmake)
    set(OPENSSL_INSTALL_COMMAND nmake install_sw install_ssldirs)
    set(OPENSSL_SSL_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libssl.lib)
    set(OPENSSL_CRYPTO_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libcrypto.lib)

elseif(APPLE)
    # Detect architectures to build
    if(CMAKE_OSX_ARCHITECTURES)
        set(BUILD_ARCHS ${CMAKE_OSX_ARCHITECTURES})
    else()
        set(BUILD_ARCHS ${CMAKE_SYSTEM_PROCESSOR})
    endif()

    # Check if we need a universal binary
    list(LENGTH BUILD_ARCHS NUM_ARCHS)

    if(NUM_ARCHS GREATER 1)
        # Universal binary - need to build each arch separately and combine
        message(STATUS "Building OpenSSL as universal binary for: ${BUILD_ARCHS}")

        set(ARCH_LIBS_SSL "")
        set(ARCH_LIBS_CRYPTO "")

        foreach(ARCH ${BUILD_ARCHS})
            if(ARCH STREQUAL "arm64")
                set(OPENSSL_PLATFORM "darwin64-arm64-cc")
            else()
                set(OPENSSL_PLATFORM "darwin64-x86_64-cc")
            endif()

            set(ARCH_INSTALL_DIR ${CMAKE_BINARY_DIR}/deps/openssl-${ARCH})

            ExternalProject_Add(openssl_${ARCH}
                    URL ${OPENSSL_URL}
                    URL_HASH SHA256=14c826f07c7e433706fb5c69fa9e25dab95684844b4c962a2cf1bf183eb4690e
                    CONFIGURE_COMMAND ./Configure ${OPENSSL_PLATFORM} no-shared no-tests
                    --prefix=${ARCH_INSTALL_DIR}
                    --openssldir=${ARCH_INSTALL_DIR}
                    BUILD_COMMAND make -j8
                    INSTALL_COMMAND make install_sw install_ssldirs
                    BUILD_IN_SOURCE 1
                    BUILD_BYPRODUCTS
                    ${ARCH_INSTALL_DIR}/lib/libssl.a
                    ${ARCH_INSTALL_DIR}/lib/libcrypto.a
                    LOG_DOWNLOAD 1
                    LOG_CONFIGURE 1
                    LOG_BUILD 1
                    LOG_INSTALL 1
            )

            list(APPEND ARCH_LIBS_SSL ${ARCH_INSTALL_DIR}/lib/libssl.a)
            list(APPEND ARCH_LIBS_CRYPTO ${ARCH_INSTALL_DIR}/lib/libcrypto.a)
        endforeach()

        # Create universal binaries using lipo
        file(MAKE_DIRECTORY ${OPENSSL_INSTALL_DIR}/lib)
        file(MAKE_DIRECTORY ${OPENSSL_INSTALL_DIR}/include)

        add_custom_command(
                OUTPUT ${OPENSSL_INSTALL_DIR}/lib/libssl.a
                COMMAND lipo -create ${ARCH_LIBS_SSL} -output ${OPENSSL_INSTALL_DIR}/lib/libssl.a
                DEPENDS ${ARCH_LIBS_SSL}
                COMMENT "Creating universal libssl.a"
        )

        add_custom_command(
                OUTPUT ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a
                COMMAND lipo -create ${ARCH_LIBS_CRYPTO} -output ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a
                DEPENDS ${ARCH_LIBS_CRYPTO}
                COMMENT "Creating universal libcrypto.a"
        )

        # Copy headers from first architecture (they're identical)
        list(GET BUILD_ARCHS 0 FIRST_ARCH)
        add_custom_command(
                OUTPUT ${OPENSSL_INSTALL_DIR}/include/openssl/ssl.h
                COMMAND ${CMAKE_COMMAND} -E copy_directory
                ${CMAKE_BINARY_DIR}/deps/openssl-${FIRST_ARCH}/include
                ${OPENSSL_INSTALL_DIR}/include
                DEPENDS openssl_${FIRST_ARCH}
                COMMENT "Copying OpenSSL headers"
        )

        # Create a custom target that depends on the lipo commands
        add_custom_target(openssl_universal ALL
                DEPENDS
                ${OPENSSL_INSTALL_DIR}/lib/libssl.a
                ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a
                ${OPENSSL_INSTALL_DIR}/include/openssl/ssl.h
        )

        foreach(ARCH ${BUILD_ARCHS})
            add_dependencies(openssl_universal openssl_${ARCH})
        endforeach()

        set(OPENSSL_EXTERNAL_TARGET openssl_universal)

    else()
        # Single architecture build
        list(GET BUILD_ARCHS 0 ARCH)

        if(ARCH STREQUAL "arm64")
            set(OPENSSL_PLATFORM "darwin64-arm64-cc")
        else()
            set(OPENSSL_PLATFORM "darwin64-x86_64-cc")
        endif()

        message(STATUS "Building OpenSSL for single architecture: ${ARCH}")

        ExternalProject_Add(openssl_external
                URL ${OPENSSL_URL}
                URL_HASH SHA256=14c826f07c7e433706fb5c69fa9e25dab95684844b4c962a2cf1bf183eb4690e
                CONFIGURE_COMMAND ./Configure ${OPENSSL_PLATFORM} no-shared no-tests
                --prefix=${OPENSSL_INSTALL_DIR}
                --openssldir=${OPENSSL_INSTALL_DIR}
                BUILD_COMMAND make -j8
                INSTALL_COMMAND make install_sw install_ssldirs
                BUILD_IN_SOURCE 1
                BUILD_BYPRODUCTS
                ${OPENSSL_INSTALL_DIR}/lib/libssl.a
                ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a
                ${OPENSSL_INSTALL_DIR}/include/openssl/ssl.h
                LOG_DOWNLOAD 1
                LOG_CONFIGURE 1
                LOG_BUILD 1
                LOG_INSTALL 1
        )

        set(OPENSSL_EXTERNAL_TARGET openssl_external)
    endif()

    set(OPENSSL_SSL_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libssl.a)
    set(OPENSSL_CRYPTO_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a)

else() # Linux
    set(OPENSSL_CONFIGURE_COMMAND
            ./config no-shared no-tests
            --prefix=${OPENSSL_INSTALL_DIR}
            --openssldir=${OPENSSL_INSTALL_DIR}
            -fPIC
    )
    set(OPENSSL_BUILD_COMMAND make -j8)
    set(OPENSSL_INSTALL_COMMAND make install_sw install_ssldirs)
    set(OPENSSL_SSL_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libssl.a)
    set(OPENSSL_CRYPTO_LIBRARY ${OPENSSL_INSTALL_DIR}/lib/libcrypto.a)

    ExternalProject_Add(openssl_external
            URL ${OPENSSL_URL}
            URL_HASH SHA256=14c826f07c7e433706fb5c69fa9e25dab95684844b4c962a2cf1bf183eb4690e
            CONFIGURE_COMMAND ${OPENSSL_CONFIGURE_COMMAND}
            BUILD_COMMAND ${OPENSSL_BUILD_COMMAND}
            INSTALL_COMMAND ${OPENSSL_INSTALL_COMMAND}
            BUILD_IN_SOURCE 1
            BUILD_BYPRODUCTS
            ${OPENSSL_SSL_LIBRARY}
            ${OPENSSL_CRYPTO_LIBRARY}
            ${OPENSSL_INSTALL_DIR}/include/openssl/ssl.h
            LOG_DOWNLOAD 1
            LOG_CONFIGURE 1
            LOG_BUILD 1
            LOG_INSTALL 1
    )

    set(OPENSSL_EXTERNAL_TARGET openssl_external)
endif()

# Create include directory ahead of time
file(MAKE_DIRECTORY ${OPENSSL_INSTALL_DIR}/include)

# ============================================================================
# Create Imported Targets
# ============================================================================
add_library(OpenSSL::SSL STATIC IMPORTED GLOBAL)
add_library(OpenSSL::Crypto STATIC IMPORTED GLOBAL)

set_target_properties(OpenSSL::SSL PROPERTIES
        IMPORTED_LOCATION ${OPENSSL_SSL_LIBRARY}
        INTERFACE_INCLUDE_DIRECTORIES ${OPENSSL_INSTALL_DIR}/include
)

set_target_properties(OpenSSL::Crypto PROPERTIES
        IMPORTED_LOCATION ${OPENSSL_CRYPTO_LIBRARY}
        INTERFACE_INCLUDE_DIRECTORIES ${OPENSSL_INSTALL_DIR}/include
)

# Ensure OpenSSL is built before targets that depend on it
add_dependencies(OpenSSL::SSL ${OPENSSL_EXTERNAL_TARGET})
add_dependencies(OpenSSL::Crypto ${OPENSSL_EXTERNAL_TARGET})

# ============================================================================
# Platform-Specific System Libraries for OpenSSL
# ============================================================================
if(WIN32)
    # Windows system libraries required by static OpenSSL
    set_property(TARGET OpenSSL::SSL APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES ws2_32 crypt32
    )
    set_property(TARGET OpenSSL::Crypto APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES ws2_32 crypt32
    )

elseif(UNIX AND NOT APPLE)
    # Linux system libraries required by static OpenSSL
    set_property(TARGET OpenSSL::SSL APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES dl pthread
    )
    set_property(TARGET OpenSSL::Crypto APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES dl pthread
    )
endif()

# Set OpenSSL variables for compatibility with FindOpenSSL
set(OPENSSL_FOUND TRUE CACHE BOOL "OpenSSL found" FORCE)
set(OPENSSL_INCLUDE_DIR ${OPENSSL_INSTALL_DIR}/include CACHE PATH "OpenSSL include directory" FORCE)
set(OPENSSL_SSL_LIBRARY ${OPENSSL_SSL_LIBRARY} CACHE FILEPATH "OpenSSL SSL library" FORCE)
set(OPENSSL_CRYPTO_LIBRARY ${OPENSSL_CRYPTO_LIBRARY} CACHE FILEPATH "OpenSSL Crypto library" FORCE)
set(OPENSSL_LIBRARIES ${OPENSSL_SSL_LIBRARY} ${OPENSSL_CRYPTO_LIBRARY} CACHE STRING "OpenSSL libraries" FORCE)

if(NUM_ARCHS GREATER 1)
    message(STATUS "OpenSSL ${OPENSSL_VERSION} will be built as universal binary")
else()
    message(STATUS "OpenSSL ${OPENSSL_VERSION} will be built from source")
endif()
message(STATUS "OpenSSL install directory: ${OPENSSL_INSTALL_DIR}")

function(configure_for_openssl TARGET_NAME)
    # Platform-specific libraries for keychain
    if(WIN32)
        target_link_libraries(${TARGET_NAME} PRIVATE
                advapi32  # For Credential Manager
        )

    elseif(UNIX AND NOT APPLE)
        # For Secret Service on Linux
        find_package(PkgConfig REQUIRED)
        pkg_check_modules(LIBSECRET REQUIRED libsecret-1)
        target_include_directories(${TARGET_NAME} PRIVATE ${LIBSECRET_INCLUDE_DIRS})
        target_link_libraries(${TARGET_NAME} PRIVATE ${LIBSECRET_LIBRARIES})

    elseif(APPLE)
        find_library(SECURITY_FRAMEWORK Security REQUIRED)
        find_library(COREFOUNDATION_FRAMEWORK CoreFoundation REQUIRED)
        target_link_libraries(${TARGET_NAME} PRIVATE
                ${SECURITY_FRAMEWORK}
                ${COREFOUNDATION_FRAMEWORK}
        )
    endif()

    # Compiler warnings
    if(MSVC)
        target_compile_options(${TARGET_NAME} PRIVATE /W4)
    else()
        target_compile_options(${TARGET_NAME} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endfunction()