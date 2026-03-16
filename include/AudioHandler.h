// -> include/AudioHandler.h
#pragma once

// OS Detection & Includes 
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib") // Link Winsock on Windows
typedef int socklen_t;
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>
#define INVALID_SOCKET -1
#define SOCKET_ERROR -1
#endif

#include <miniaudio.h>
#include <SDL2/SDL.h>
#include <iostream>
#include <atomic>
#include <vector>


// -> Forward declaration: NetworkHandler class ki existence batata hai 
// -> taaki unnecessary header files include na karni padein.
class NetworkHandler;

// -> AudioHandler class: Microphone se audio capture karne aur use NetworkHandler ke zariye stream karne ka kaam hai...
class NetworkHandler;

struct AudioContext {
    NetworkHandler* net;
};

class AudioHandler {
public:
// -> Constructor: Variables ko default values pe set karta hai...
    AudioHandler();

// -> Destructor: Program band hone par resources (mic device) ko safe tarike se release karta hai.
    ~AudioHandler();

// -> Audio device ko setup karta hai aur use network handler se connect karta hai...
// -> network: NetworkHandler ka pointer jahan audio data bheja jayega...
// -> return: true agar initialization successful ho, warna false...
    bool init(NetworkHandler* network);

    AudioHandler(int port);
    ~AudioHandler();

    bool initRecorder(NetworkHandler* network);
    bool startRecording();
    void stopRecording();

    bool initPlayer();
    void startListening();

private:
    ma_device device; // -> Miniaudio ki core structure jo hardware (mic) ko represent karti hai...
    NetworkHandler* netHandler; // -> Pointer to network handler jahan audio data bheja jayega...
    bool isInitialized; // -> Audio device initialized hai ya nahi, taaki startRecording se pehle check kar sakein...
    bool isRecording; // -> Recording chal rahi hai ya nahi, taaki stopRecording sahi se kaam kare...
    void cleanup();

    // Recorder
    ma_device device;
    bool isRecorderInitialized;
    bool isRecording;
    AudioContext contextPacket;

    // Player (Cross-Platform Sockets)
#ifdef _WIN32
    SOCKET server_fd;
    SOCKET new_socket;
#else
    int server_fd;
    int new_socket;
#endif

    int port;
    SDL_AudioDeviceID audioDevice;
    SDL_AudioSpec audioSpec;
    bool isPlayerInitialized;
};