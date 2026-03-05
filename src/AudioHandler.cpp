#define MINIAUDIO_IMPLEMENTATION
#include "AudioHandler.h"
#include "NetworkHandler.h"
#include <cstring>

extern std::atomic<bool> is_active;
extern std::atomic<bool> is_pc_speaking;
extern std::chrono::steady_clock::time_point last_activity_time;

#define BUFFER_SIZE 4096

// Helper Macros for Cross-Platform
#ifdef _WIN32
#define CLOSE_SOCKET(s) closesocket(s)
#define READ_SOCKET(s, buf, len) recv(s, buf, len, 0)
#else
#define CLOSE_SOCKET(s) close(s)
#define READ_SOCKET(s, buf, len) read(s, buf, len)
#endif

//  [data_callback same as before] 
void data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount) {
    // (Pichla code same rahega)
    AudioContext* ctx = (AudioContext*)pDevice->pUserData;
    if (ctx == NULL || ctx->net == NULL || ctx->lowwi == NULL) return;
    const float* inputFloats = (const float*)pInput;
    std::vector<float> audio_chunk(inputFloats, inputFloats + frameCount);
    ctx->lowwi->run(audio_chunk);
    if (ctx->is_active && *(ctx->is_active)) {
        size_t dataSize = frameCount * 1 * sizeof(float);
        ctx->net->sendAudioChunk(pInput, dataSize);
    }
}

// ... [Constructors same as before] ...
AudioHandler::AudioHandler() : port(0), isRecorderInitialized(false), isPlayerInitialized(false), isRecording(false), server_fd(INVALID_SOCKET), audioDevice(0) {}
AudioHandler::AudioHandler(int p) : port(p), isRecorderInitialized(false), isPlayerInitialized(false), isRecording(false), server_fd(INVALID_SOCKET), audioDevice(0) {}
AudioHandler::~AudioHandler() { cleanup(); }

// ... [Recorder Functions same as before] ...
bool AudioHandler::initRecorder(NetworkHandler* network, CLFML::LOWWI::Lowwi* lowwi_inst, std::atomic<bool>* active_flag) {
    // (Paste previous recorder code here)
    this->contextPacket.net = network;
    this->contextPacket.lowwi = lowwi_inst;
    this->contextPacket.is_active = active_flag;
    ma_device_config deviceConfig = ma_device_config_init(ma_device_type_capture);
    deviceConfig.capture.format = ma_format_f32;
    deviceConfig.capture.channels = 1;
    deviceConfig.sampleRate = 16000;
    deviceConfig.dataCallback = data_callback;
    deviceConfig.pUserData = &this->contextPacket;
    if (ma_device_init(NULL, &deviceConfig, &device) != MA_SUCCESS) return false;
    isRecorderInitialized = true;
    return true;
}
bool AudioHandler::startRecording() { if (!isRecorderInitialized) return false; return ma_device_start(&device) == MA_SUCCESS; }
void AudioHandler::stopRecording() { if (isRecorderInitialized) ma_device_stop(&device); }

// --- PLAYER IMPLEMENTATION (Fixed for Windows) ---
bool AudioHandler::initPlayer() {
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        std::cerr << "SDL Error: " << SDL_GetError() << std::endl;
        return false;
    }

    // Windows Sockets Init
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed" << std::endl;
        return false;
    }
#endif

    SDL_zero(audioSpec);
    audioSpec.freq = 24000;
    audioSpec.format = AUDIO_F32SYS;
    audioSpec.channels = 1;
    audioSpec.samples = 1024;
    audioSpec.callback = NULL;

    audioDevice = SDL_OpenAudioDevice(NULL, 0, &audioSpec, NULL, 0);
    if (audioDevice == 0) return false;

    SDL_PauseAudioDevice(audioDevice, 0);
    isPlayerInitialized = true;
    return true;
}
void AudioHandler::startListening() {
    if (!isPlayerInitialized) return;

    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
        perror("Socket failed");
        return;
    }

    // Windows pe SO_REUSEPORT nahi hota, sirf SO_REUSEADDR
#ifdef _WIN32
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
#else
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));
#endif

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        return;
    }

    if (listen(server_fd, 3) < 0) {
        perror("Listen");
        return;
    }

    
    while (true) {
        if ((new_socket = accept(server_fd, (struct sockaddr*)&address, (socklen_t*)&addrlen)) == INVALID_SOCKET) {
            continue;
        }

        char buffer[BUFFER_SIZE];
        int bytesRead;

        // PC se aane wala data read kar rahe hain
        while ((bytesRead = READ_SOCKET(new_socket, buffer, BUFFER_SIZE)) > 0) {
            is_pc_speaking = true; // System ko bata ki PC bol raha hai
            last_activity_time = std::chrono::steady_clock::now(); // Timer reset

            SDL_QueueAudio(audioDevice, buffer, bytesRead);
        }

        is_pc_speaking = false; // Jab audio aana band ho jaye
        CLOSE_SOCKET(new_socket);
    }
}

void AudioHandler::cleanup() {
    if (isRecorderInitialized) {
        ma_device_uninit(&device);
        isRecorderInitialized = false;
    }
    if (isPlayerInitialized) {
        if (server_fd != INVALID_SOCKET) CLOSE_SOCKET(server_fd);
        if (audioDevice > 0) SDL_CloseAudioDevice(audioDevice);
        SDL_Quit();
#ifdef _WIN32
        WSACleanup();
#endif
        isPlayerInitialized = false;
    }
}