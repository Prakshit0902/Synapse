#include <iostream>
#include <thread>
#include <chrono>
#include <opencv2/opencv.hpp>

// Project Headers
#include "CameraHandler.hpp"
#include "NetworkHandler.h"
#include "AudioHandler.h"

using namespace std;

int main(int argc, char* argv[]) {
    std::cout << "Synapse: CONTINUOUS STREAMING STARTUP" << std::endl;

    // 1. HARDWARE & NETWORK SETUP
    CameraHandler ch;
    bool camerReady = false;
    for (int i = 0; i < 5; i++) {
        if (ch.initCamera(0)) {
            cameraReady = true;
            break;
        }
        std::cout << "[WARNING] Camera busy, retrying in 1s... (" << i + 1 << "/5)" << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    if (ch.initCamera(0)) {
        std::cerr << "[ERROR] Camera Initialization Failed!" << std::endl;
        return -1;
    }

    NetworkHandler nh_video;
    nh_video.init("tcp://*:5555"); // Video Stream PC ko bhejega

    NetworkHandler nh_audio;
    nh_audio.init("tcp://*:5556"); // Audio Stream PC ko bhejega


    // 2. AUDIO PLAYER (PC se aawaz sunega aur Speaker pe bajayega)
    AudioHandler* player = new AudioHandler(5000);
    if (!player->initPlayer()) {
        std::cerr << "[ERROR] Player Initialization failed!" << std::endl;
    }
    else {
        std::thread audioThread([player]() {
            player->startListening();
            });
        audioThread.detach();
        std::cout << "[OK] Audio Player Service Started on Port 5000" << std::endl;
    }


    // 3. AUDIO RECORDER (Mic se lagatar sunega aur PC ko bhejega)
    AudioHandler recorder;
    // 
    if (!recorder.initRecorder(&nh_audio)) {
        std::cerr << "[ERROR] Audio Recorder Init Failed!" << std::endl;
        return -1;
    }

    recorder.startRecording();
    std::cout << "[OK] System Listening and Streaming Audio continuously..." << std::endl;

    // 4. MAIN VIDEO LOOP (Lagatar Frames bhejega)
    std::cout << "[OK] Streaming Video continuously..." << std::endl;
    while (true) {
    cv::Mat frame = ch.getFrame();
    if (frame.empty()) {
        std::cout << "[WARNING] Camera returning empty frames!" << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        continue;
    }

    std::cout << "-> Sending Frame to PC..." << std::endl; // YE LINE DAAL
    nh_video.sendFrame(frame);
}

    // Cleanup
    recorder.stopRecording();
    delete player;
    std::cout << "SYSTEM SHUTDOWN " << std::endl;
    return 0;
}