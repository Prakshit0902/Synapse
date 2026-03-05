#include <iostream>
#include <thread> 
#include <chrono>
#include <atomic> 
#include <opencv2/opencv.hpp>

// Project Headers
#include "CameraHandler.hpp"
#include "NetworkHandler.h"
#include "AudioHandler.h"
#include "lowwi.hpp"

using namespace std;
using namespace CLFML::LOWWI;

// Global System State Flag
// Global System State Flag
std::atomic<bool> is_active(false);
std::chrono::steady_clock::time_point last_activity_time;


int main(int argc, char* argv[]) {
    std::cout << "--- TRINETRA VISION: SYSTEM STARTUP ---" << std::endl;

    // 1. HARDWARE & NETWORK SETUP
    
    CameraHandler ch;
    if (!ch.initCamera(0)) {
        std::cerr << "[ERROR] Camera Initialization Failed!" << std::endl;
        return -1;
    }

    NetworkHandler nh_video;
    nh_video.init("tcp://*:5555"); // Video Stream

    NetworkHandler nh_audio;
    nh_audio.init("tcp://*:5556"); // Audio Stream

   
    // 2. AUDIO PLAYER (PC -> RPi Speaker) - RUN IN THREAD

    // Hum heap pe object banayenge taaki thread safety rahe
    AudioHandler* player = new AudioHandler(5000);

    if (!player->initPlayer()) { // Maine naam clear kar diya hai (initPlayer)
        std::cerr << "Player Initialization failed!" << std::endl;
    }
    else {
        // Isko alag thread mein daal diya
        std::thread audioThread([player]() {
            player->startListening();
            });
        audioThread.detach(); // Background mein chalta rahega
        std::cout << "[OK] Audio Player Service Started on Port 5000" << std::endl;
    }


    // 3. WAKE WORD ENGINE SETUP (Lowwi)
 
    Lowwi ww_runtime;
    Lowwi_word_t ww;
    ww.model_path = "hey_jarvis.onnx";
    ww.phrase = "Hey Jarivs";
    ww.threshold = 0.5;
    

    ww.cbfunc = [](CLFML::LOWWI::Lowwi_ctx_t ctx, std::shared_ptr<void> user_data) {
        std::cout << "\n[EVENT] Wake Word Detected! | System ACTIVATE" << std::endl;
        is_active = true;

        //  NEW: Reset the timer
        last_activity_time = std::chrono::steady_clock::now();
        };
    ww_runtime.add_wakeword(ww);

    // 4. AUDIO RECORDER (Mic -> RPi -> PC)
    AudioHandler recorder; // Default constructor handles recording
    if (!recorder.initRecorder(&nh_audio, &ww_runtime, &is_active)) {
        std::cerr << "[ERROR] Audio Recorder Init Failed!" << std::endl;
        return -1;
    }

    recorder.startRecording();
    std::cout << "[OK] System Listening. Waiting for 'Hey Synapse'..." << std::endl;

    // 5. MAIN VIDEO LOOP
    while (true) {
        cv::Mat frame = ch.getFrame();
        if (frame.empty()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }

        if (is_active) {
            //  TIMER CHECK 
            auto now = std::chrono::steady_clock::now();
            // Calculate kitne seconds beet gaye
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - last_activity_time).count();

            if (elapsed > 20) {
                // TIMEOUT: 20 second ho gaye, wapas Standby me jao
                std::cout << "💤 Inactivity Timeout. Going to Standby..." << std::endl;
                is_active = false;
            }
            else {
                // ACTIVE: Abhi time bacha hai, Frame bhejo
                nh_video.sendFrame(frame);

                // Visuals (Green Box + Timer Display)
                //cv::rectangle(frame, cv::Point(0, 0), cv::Point(frame.cols, frame.rows), cv::Scalar(0, 255, 0), 10);

                // Optional: Screen pe dikhao ki kitna time bacha hai sone me
                //std::string status = "ONLINE (" + std::to_string(20 - elapsed) + "s)";
                //cv::putText(frame, status, cv::Point(30, 50), cv::FONT_HERSHEY_SIMPLEX, 1, cv::Scalar(0, 255, 0), 2);
            }
        }
        else {

            // STANDBY MODE 
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            //cv::putText(frame, "STANDBY - Say 'Hey Synapse'", cv::Point(30, 50), cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 0, 255), 2);
        }

        //cv::imshow("Trinetra Vision", frame);
        //if (cv::waitKey(1) == 27) break;
    }

    // Cleanup
    recorder.stopRecording();
    delete player; // Cleanup player
    std::cout << "SYSTEM SHUTDOWN " << std::endl;
    return 0;
}