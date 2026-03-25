

# SYNAPSE: Distributed Edge-Cloud AI Assistant Architecture
**Powering *Naina* | Built from Scratch with Linux Environments**

<div align="center">
  <img src="https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/GNU%20Bash-4EAA25?style=for-the-badge&logo=GNU%20Bash&logoColor=white" />
  <img src="https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white" />
  <img src="https://img.shields.io/badge/ZeroMQ-DF0000?style=for-the-badge&logo=ZeroMQ&logoColor=white" />
  <img src="https://img.shields.io/badge/NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
  <img src="https://img.shields.io/badge/CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" />
</div>

<br>

Synapse is the robust, multi-threaded distributed architecture built from scratch to power **Naina**, a highly dynamic personal AI assistant. 

Unlike standard API wrappers, Synapse solves the heavy-compute problemassets/synapse-hld-nodes-based.png of modern LLMs and vision models by splitting the workload: a **Raspberry Pi 3** acts as the sensory edge device (mouth, eyes and ears) written purely in raw poer (C++), while a powerful **Local PC** acts as the brain (inference server) fully leveraging **NVIDIA CUDA** for parallel GPU computing.

<img src="https://cdn.pixabay.com/photo/2024/04/08/19/56/neural-network-8684318_1280.jpg">

## High Level Design 
<img src="assets/synapse-hld-nodes-based.png"  width="20000">

## Key Capabilities

* **Real-Time Edge Perception:** RPi 3 directly captures video (V2 Camera) and audio, applies raw OpenCV MPEG compression, and streams it over LAN with nearly zero latency.
* **CUDA-Accelerated Conversational AI:** Heavy lifting is done entirely on the GPU. Powered by OpenAI's **Whisper** (distil-large-v3) for real-time transcription and **Ollama (Qwen 2.5 - 3B)** for insanely fast, context-aware, and chatty responses.
* **Dynamic Action Execution:** Naina doesn't just talk; she acts. Ask for the current weather, and she dynamically fetches the real-time API data to tell you if you need a jacket.
* **Long-Term RAG Memory:** "Remember Ankit, he is a DSA legend." Synapse embeds and stores user-defined facts in **ChromaDB**. Ask about Ankit weeks later, and Naina will instantly recall.
* **Hardcoded Facial Recognition:** Utilizes **InsightFace** to scan incoming frames and match them against a pre-indexed directory of labeled images, identifying exactly who is standing in front of the camera.
* **Human-like Voice:** Text responses are synthesized through **Kokoro TTS** and streamed back to the RPi speaker for a seamless conversational loop.

##  System Architecture

The system is strictly divided into two independent nodes communicating over a Local Area Network (LAN). 

### 1. The Edge Node (Raspberry Pi 3)
* **Environment:** Bare-metal execution.
* **Tech Stack:** Pure C++, OpenCV, SDL2, Miniaudio, ZeroMQ.
* **Function:** Captures raw video frames (V2 Camera) and audio. To prevent the RPi from choking, it applies real-time OpenCV MPEG compression in C++ before transmitting the data over the network.

### 2. The Core Server (Local Machine / GPU Node)
* **Environment:** Linux-native daemon processes.
* **Tech Stack:** Python, ZeroMQ, cuDNN (12.3), OpenAI Whisper (distil-large-v3), Ollama (Qwen 2.5 - 3B), Kokoro TTS, InsightFace, ChromaDB.
* **Function:** A multi-threaded Python backend that accepts the socket stream asynchronously. It handles word detection, pushes audio and vision tasks to the GPU for inference, generates RAG-backed responses, synthesizes speech, and streams the audio back to the Rpi.

###  Network & Shell Orchestration
* **ZeroMQ (ZMQ):** Used for asynchronous, high-throughput, low-latency Inter-Process Communication (IPC) and network socket streaming between the C++ client and Python server.
* **Bash/Shell Scripting:** The entire startup sequence, network binding, environment variable management, and process daemonization on both the RPi and the  server are heavily automated using pipelines of processing.
## 📹 Demo
* Dropping soon

## The Developer Diaries: Building Synapse

Building this wasn't a walk in the park. Bridging low-level C++ with modern Python AI stacks is an absolute bloodbath. 

*We will be documenting this entire engineering journey as a multi-part "Web Series" style Devlog on Medium. (Links dropping soon).*

* **Episode 1: The Edge Struggle.** Why we chose pure C++ for the Pi, fighting with SDL2/Miniaudio, and writing custom OpenCV MPEG compression to kill latency.
* **Episode 2: Networking Hell.** Tying the Pi and PC together. Why standard HTTP failed and how ZeroMQ + pipelining saved the day.
* **Episode 3: The GPU Brain Transplant.** Managing VRAM limits and tuning the Whisper -> Qwen 2.5 -> Kokoro TTS pipeline for sub-second conversational speeds using CUDA.
* **Episode 4: Memory & Vision.** The transition from a tedious dynamic face-saving approach to a rock-solid hardcoded InsightFace directory, and plugging in ChromaDB for permanent memory.

## 🛣️ Roadmap

- [ ] Publish comprehensive latency and resource utilization metrics (RPi CPU vs. PC GPU/VRAM).
- [ ] Make a Docker file to run this AI in a local environment, so you don't go through dependency hell.
- [ ] Intensively documenting every file.
- [ ] Make script file for running as background service.
---
*Built with grit, C++, and lots of tea ☕.*