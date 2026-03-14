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


class NetworkHandler;

struct AudioContext {
    NetworkHandler* net;
};

class AudioHandler {
public:
    AudioHandler();
    AudioHandler(int port);
    ~AudioHandler();

    bool initRecorder(NetworkHandler* network);
    bool startRecording();
    void stopRecording();

    bool initPlayer();
    void startListening();

private:
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