import zmq
import numpy as np
import threading
import time
import cv2 as cv
import os

from python.engine.main import Synapse


class EdgeBridge:
    def __init__(self):
        print("Starting Synapse Edge Bridge...")

        self.app = Synapse()

        # Networking Constants
        self.VIDEO_PORT = "5555"
        self.AUDIO_PORT = "5556"
        self.SILENCE_THRESHOLD = 0.01  # Aawaz ka threshold
        self.SILENCE_DURATION = 1.0  # 1 second chup = sentence complete

    def process_command(self, command):
        """MIMIC OF MAIN.PY LOGIC: Agentic processing -> TTS"""
        if not command: return

        print(f"\n🎤 Edge Heard: {command}")
        command_lower = command.lower()

        # 1. Check Exit
        if self.app.check_exit(command_lower):
            self.app.mouth.speak_for_rpi("Goodbye! Shutting down edge connection.")
            print("Stopping Edge Synapse...")
            os._exit(0)

        # 2. Agentic Approach
        print(f"🤖 Processing with Agent: {command}")
        agentic_response = self.app.brain.run_agentic_llm(command)

        # Registration check
        if agentic_response and "[REGISTER]" in agentic_response:
            print("🚀 Triggering Edge Registration flow...")
            # (You can map this to a modified edge_registration flow later)
            self.app.mouth.speak_for_rpi("Registration initiated from edge.")
            return

        # Normal Agent Response
        if agentic_response and "I encountered" not in agentic_response:
            print(f"🤖 Agent Response: {agentic_response}")
            if "Starting music:" in agentic_response:
                print("[System] Music starting - Edge mode")
                self.app.manual_music_mode = True
            else:
                self.app.mouth.speak_for_rpi(agentic_response)  # Send to C++
            return

        # 3. Fallback
        print(f"💬 Falling back to Chat: {command}")
        ai_response = self.app.brain.chat(command)
        self.app.mouth.speak_for_rpi(ai_response)  # Send to C++

    def audio_listener(self):
        context = zmq.Context()
        socket_audio = context.socket(zmq.SUB)
        socket_audio.connect(f"tcp://192.168.1.52:{self.AUDIO_PORT}")
        socket_audio.setsockopt_string(zmq.SUBSCRIBE, '')


        poller = zmq.Poller()
        poller.register(socket_audio, zmq.POLLIN)

        print(f"👂 Edge Audio Listening on {self.AUDIO_PORT}...")

        audio_buffer = []
        is_speaking = False
        last_speech_time = time.time()

        while True:
            try:
                # 100ms ka timeout. Agar data nahi hai toh loop aage badhega
                socks = dict(poller.poll(100))

                if socket_audio in socks and socks[socket_audio] == zmq.POLLIN:
                    packet = socket_audio.recv(flags=zmq.NOBLOCK)
                    chunk = np.frombuffer(packet, dtype=np.float32)
                    volume = np.sqrt(np.mean(chunk ** 2))

                    if volume > self.SILENCE_THRESHOLD:
                        if not is_speaking:
                            print("User Speaking...", end="\r")
                            is_speaking = True
                        audio_buffer.append(chunk)
                        last_speech_time = time.time()

                # Silence logic ab if/else ke bahar bhi check ho sakta hai
                # kyunki poller timeout dega aur loop chalega
                if is_speaking and (time.time() - last_speech_time) > self.SILENCE_DURATION:
                    print("\nTranscribing...")
                    full_audio = np.concatenate(audio_buffer)
                    text = self.app.ear.transcribe_raw(full_audio)

                    if text:
                        self.process_command(text)

                    is_speaking = False
                    audio_buffer = []
                    print("Edge Audio Listening...", end="\r")

            except Exception as e:
                print(f"Audio Error: {e}")
                break

    def video_listener(self):
        context = zmq.Context()
        socket_video = context.socket(zmq.SUB)
        socket_video.subscribe(b"")
        socket_video.connect(f"tcp://192.168.1.52:{self.VIDEO_PORT}")
        print(f"Edge Video Receiver started on {self.VIDEO_PORT}... Waiting for Pi...")

        first_frame = True  # Tracker laga diya

        while True:
            try:
                packet = socket_video.recv(flags=zmq.NOBLOCK)
                np_arr = np.frombuffer(packet, dtype=np.uint8)
                frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)

                if frame is not None:
                    if first_frame:
                        print("\nSUCCESS: First Video Frame Received from Pi! Connection Active.")
                        first_frame = False

                    cv.imshow("TRINETRA EDGE VISION", frame)

                if cv.waitKey(1) == ord('q'):
                    break

            except zmq.Again:
                # Ye normal hai jab tak naya frame nahi aata
                pass
            except Exception as e:
                # Agar koi aur error hai toh ab chup nahi baithega
                print(f"Video Receiver Error: {e}")

    def start(self):
        t_audio = threading.Thread(target=self.audio_listener)
        t_audio.daemon = True
        t_audio.start()

        self.video_listener()


if __name__ == "__main__":
    bridge = EdgeBridge()
    bridge.start()