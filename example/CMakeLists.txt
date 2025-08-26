cmake_minimum_required(VERSION 3.16)
project(ParticleSimulator)

#set(VCPKG_DEFAULT_HOST_TRIPLET x64-windows)
#set(VCPKG_TARGET_TRIPLET x64-windows)
#set(VCPKG_MANIFEST_INSTALL ON)
#set(VCPKG_MANIFEST_MODE ON)
#set(VCPKG_ROOT "C:/vcpkg" CACHE STRING "eVcpkg root directory")
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake-modules")
message(STATUS "VC Package root found here: ${VCPKG_ROOT}")
# Set the vcpkg toolchain file
set(CMAKE_TOOLCHAIN_FILE "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
		CACHE STRING "Vcpkg toolchain file")
if(EXISTS "${CMAKE_TOOLCHAIN_FILE}")
	include(${CMAKE_TOOLCHAIN_FILE})
endif()

set(CMAKE_CXX_STANDARD 20)

set(CMAKE_VERBOSE_MAKEFILE ON)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake-modules")

#set(Hedgehog_DIR "/path/to/hedgehog")
# Need to define variable Hedgehog_INCLUDE_DIR to the hedgehog path
# hedgehog
find_package(Hedgehog REQUIRED)

# OpenBLAS
find_package(OpenBLAS QUIET)

# Cuda
find_package(NVTX QUIET)

set(CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS} ${Hedgehog_CXX_FLAGS})

if (NOT MSVC)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wextra -Werror -pedantic")
endif (NOT MSVC)

#Gather tclap headers
#file(GLOB tclap_headers "../../../utils/tclap/*.h")

# Add tutorials target
add_subdirectory(particle_simulator)