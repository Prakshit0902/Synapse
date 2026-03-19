cmake_minimum_required(VERSION 3.15)
project(Synapse) 

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. SETUP SOURCES & INCLUDES
include_directories(include)

# Apni saari source files yahan add karo
set(SOURCES 
    src/main.cpp   
    src/CameraHandler.cpp 
    src/NetworkHandler.cpp
    src/AudioHandler.cpp
    # Headers ko source me add karne se VS me dikhte hain
    include/NetworkHandler.h         
    include/CameraHandler.hpp    
    include/AudioHandler.h
)

# 2. PLATFORM SPECIFIC SETUP
if(WIN32)
    #  WINDOWS (Local Debugging)
    message(STATUS "Windows Detected - Using Vcpkg paths")
    
    find_package(OpenCV REQUIRED)
    find_package(cppzmq CONFIG REQUIRED)
    find_package(SDL2 CONFIG REQUIRED)

    # Miniaudio Fix for Windows
    find_path(MINIAUDIO_PATH NAMES miniaudio.h REQUIRED)
    include_directories(${MINIAUDIO_PATH})
    
    add_executable(${PROJECT_NAME} ${SOURCES})

    # Windows Linking (ONNX aur Lowwi hata diye)
    target_link_libraries(${PROJECT_NAME} PRIVATE 
        ${OpenCV_LIBS} 
        cppzmq
        SDL2::SDL2 
        SDL2::SDL2main
    )

else()
    #  RASPBERRY PI / LINUX (Remote Build)
    message(STATUS " Raspberry Pi Detected - Setting up Manual Paths")
    
    set(RPI_LIBS_DIR "/home/pi/my_libs")
        
    # 1. Find Packages
    find_package(OpenCV REQUIRED)
    find_package(PkgConfig REQUIRED)
    find_package(Threads REQUIRED)
    find_package(ALSA REQUIRED)
    
    # SDL2 ADD KARO 
    pkg_check_modules(SDL2 REQUIRED sdl2) 

    # ZMQ Check
    pkg_check_modules(ZMQ libzmq REQUIRED)
  
    # 2. Includes
    include_directories(${RPI_LIBS_DIR})
    include_directories(${SDL2_INCLUDE_DIRS}) # SDL2 ke headers yahan hain

    add_executable(${PROJECT_NAME} ${SOURCES})

    # 3. Final Linking (ONNX aur lowwi hata diye)
    target_link_libraries(${PROJECT_NAME} PRIVATE 
        ${OpenCV_LIBS} 
        ${ZMQ_LIBRARIES}
        ${ALSA_LIBRARIES}
        ${SDL2_LIBRARIES}  # SDL2 Link karo
      
        pthread
        atomic
    )
endif()