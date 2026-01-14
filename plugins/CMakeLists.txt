# CMake configuration for Video-Code plugins
#
# This file provides functions to build plugins as shared libraries.

cmake_minimum_required(VERSION 3.20)

# Function to build a C++ plugin
function(add_plugin_cpp PLUGIN_NAME PLUGIN_TYPE SOURCE_FILE)
    set(TARGET_NAME ${PLUGIN_NAME}_cpp)
    
    add_library(${TARGET_NAME} SHARED ${SOURCE_FILE})
    
    # Set output name to match plugin.json
    set_target_properties(${TARGET_NAME} PROPERTIES
        OUTPUT_NAME "${PLUGIN_NAME}_cpp"
        PREFIX ""
        SUFFIX ".so"
    )
    
    # Include directories
    target_include_directories(${TARGET_NAME} PRIVATE
        ${CMAKE_SOURCE_DIR}/include
    )
    
    # Link against required libraries
    target_link_libraries(${TARGET_NAME} PRIVATE
        opencv_core
        opencv_imgproc
        nlohmann_json::nlohmann_json
    )
    
    # Install plugin to plugins directory
    if(${PLUGIN_TYPE} STREQUAL "transformation")
        set(PLUGIN_DIR "${CMAKE_SOURCE_DIR}/plugins/transformations/${PLUGIN_NAME}")
    elseif(${PLUGIN_TYPE} STREQUAL "input")
        set(PLUGIN_DIR "${CMAKE_SOURCE_DIR}/plugins/inputs/${PLUGIN_NAME}")
    endif()
    
    install(TARGETS ${TARGET_NAME}
        LIBRARY DESTINATION ${PLUGIN_DIR}
    )
    
    # Copy to plugin directory after build
    add_custom_command(TARGET ${TARGET_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:${TARGET_NAME}>
        ${PLUGIN_DIR}/$<TARGET_FILE_NAME:${TARGET_NAME}>
    )
endfunction()

# Function to build a Python plugin (compile to shared library)
function(add_plugin_python PLUGIN_NAME PLUGIN_TYPE SOURCE_FILE)
    # For now, we'll just document this
    # Python plugins can be kept as .py files or compiled to .so using tools like Cython
    # This is left as an exercise for the user
    
    message(STATUS "Python plugin ${PLUGIN_NAME} source: ${SOURCE_FILE}")
    message(STATUS "To compile Python plugins to .so, use Cython or similar tools")
endfunction()

# Add all plugins here
message(STATUS "Building plugins...")

# Transformation plugins
add_plugin_cpp(blur transformation 
    ${CMAKE_SOURCE_DIR}/plugins/transformations/blur/blur_cpp.cpp)

# Input plugins
add_plugin_cpp(gradient input
    ${CMAKE_SOURCE_DIR}/plugins/inputs/gradient/gradient_cpp.cpp)

message(STATUS "Plugins configured")
