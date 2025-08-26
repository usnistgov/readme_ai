find_package(SFML COMPONENTS Network Graphics Window Audio System CONFIG REQUIRED)

find_package(Hedgehog REQUIRED)

add_executable(ParticleSimulator particle_simulator.cpp)

target_link_libraries(ParticleSimulator PRIVATE SFML::Network SFML::Graphics SFML::Window SFML::Audio SFML::System)