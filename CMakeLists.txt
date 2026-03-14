cmake_minimum_required(VERSION 3.15)
project(Trinetra_Vision)

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

# --------------------------------------------------------
# 2. SETUP LOWWI (FetchContent)
# --------------------------------------------------------
include(FetchContent)
FetchContent_Declare(
  Lowwi
  GIT_REPOSITORY https://github.com/CLFML/lowwi.git
  GIT_TAG main 
)
FetchContent_MakeAvailable(Lowwi)

# --------------------------------------------------------
# 3. PLATFORM SPECIFIC SETUP
# --------------------------------------------------------
if(WIN32)
    # ==========================================
    # 🖥️ WINDOWS (Local Debugging)
    # ==========================================
    message(STATUS "🖥️ Windows Detected - Using Vcpkg paths")
    
    find_package(OpenCV REQUIRED)
    find_package(cppzmq CONFIG REQUIRED)
    find_package(SDL2 CONFIG REQUIRED)
    find_package(onnxruntime CONFIG REQUIRED)

    # Miniaudio Fix for Windows
    find_path(MINIAUDIO_PATH NAMES miniaudio.h REQUIRED)
    include_directories(${MINIAUDIO_PATH})

    add_executable(${PROJECT_NAME} ${SOURCES})

    # Windows Linking
    target_link_libraries(${PROJECT_NAME} PRIVATE 
        ${OpenCV_LIBS} 
        cppzmq
        onnxruntime
        lowwi_lib
        SDL2::SDL2 
        SDL2::SDL2main
    )

else()
    # ==========================================
    # 🍓 RASPBERRY PI / LINUX (Remote Build)
    # ==========================================
    message(STATUS "🍓 Raspberry Pi Detected - Setting up Manual Paths")

    set(RPI_LIBS_DIR "/home/pi/my_libs")
    set(ONNX_ROOT "${RPI_LIBS_DIR}/onnxruntime")

    # 1. Find Packages
    find_package(OpenCV REQUIRED)
    find_package(PkgConfig REQUIRED)
    find_package(Threads REQUIRED)
    find_package(ALSA REQUIRED)
    
    # --- SDL2 ADD KARO (Ye missing tha) ---
    pkg_check_modules(SDL2 REQUIRED sdl2) 

    # ZMQ Check
    pkg_check_modules(ZMQ libzmq REQUIRED)

    # 2. Includes
    include_directories(${RPI_LIBS_DIR})
    include_directories(${ONNX_ROOT}/include)
    include_directories(${SDL2_INCLUDE_DIRS}) # SDL2 ke headers yahan hain

    # 3. Links
    link_directories(${ONNX_ROOT}/lib)

    add_executable(${PROJECT_NAME} ${SOURCES})

    # 4. Final Linking
    target_link_libraries(${PROJECT_NAME} PRIVATE 
        ${OpenCV_LIBS} 
        ${ZMQ_LIBRARIES}
        ${ALSA_LIBRARIES}
        ${SDL2_LIBRARIES}  # SDL2 Link karo
        onnxruntime
        lowwi_lib
        dl
        pthread
        atomic
    )

    # Models copy command wahi rahegi...
    configure_file(${CMAKE_SOURCE_DIR}/hey_jarvis.onnx ${CMAKE_BINARY_DIR}/hey_jarvis.onnx COPYONLY)
    configure_file(${CMAKE_SOURCE_DIR}/melspectrogram.onnx ${CMAKE_BINARY_DIR}/melspectrogram.onnx COPYONLY)
    configure_file(${CMAKE_SOURCE_DIR}/embedding_model.onnx ${CMAKE_BINARY_DIR}/embedding_model.onnx COPYONLY)

endif()

# --------------------------------------------------------
# 4. COMMON INCLUDES FOR LOWWI
# --------------------------------------------------------
target_include_directories(${PROJECT_NAME} PRIVATE 
    ${lowwi_SOURCE_DIR}/include
    ${lowwi_SOURCE_DIR}/src
)

# --------------------------------------------------------
# 6. COPY MODELS TO BUILD FOLDER (Automatic)
# --------------------------------------------------------

# 1. Wake Word Model
configure_file(${CMAKE_SOURCE_DIR}/hey_jarvis.onnx ${CMAKE_BINARY_DIR}/hey_jarvis.onnx COPYONLY)

# 2. TTS Model (Melo)
# Naam match hona chahiye jo SCP se bheja hai
configure_file(${CMAKE_SOURCE_DIR}/melspectrogram.onnx ${CMAKE_BINARY_DIR}/melspectrogram.onnx COPYONLY)

# Aur agar embedding_model bhi use ho raha hai, toh usse bhi add kar de:
configure_file(${CMAKE_SOURCE_DIR}/embedding_model.onnx ${CMAKE_BINARY_DIR}/embedding_model.onnx COPYONLY)