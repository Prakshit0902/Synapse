import cv2 as cv
import numpy as np
import zmq
import threading
import faster_whisper
import time

# CONFIGURATION
VIDEO_PORT = "5555"
AUDIO_PORT = "5556"
SAMPLE_RATE = 16000  # C++ me 16000 set karna zaroori hai
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.0  # 1 second chup rehne par sentence complete

print("🧠 Loading Whisper Model... (Please wait)")
model = whisper.load_model("base.en")  # GPU hai to 'medium' use karein
print("✅ Model Loaded.")


# AUDIO THREAD FUNCTION
def audio_listener():
    # Audio ke liye alag socket banana padega
    context = zmq.Context()
    socket_audio = context.socket(zmq.SUB)
    socket_audio.connect(f"tcp://localhost:{AUDIO_PORT}")
    socket_audio.setsockopt_string(zmq.SUBSCRIBE, '')

    print(f"👂 Audio Thread Listening on {AUDIO_PORT}...")

    audio_buffer = []
    is_speaking = False
    last_speech_time = time.time()

    while True:
        try:
            # 1. Packet receive karo
            packet = socket_audio.recv()

            # 2. Float32 array me convert (C++ Miniaudio format)
            chunk = np.frombuffer(packet, dtype=np.float32)

            # 3. VAD Logic (Volume Check)
            volume = np.sqrt(np.mean(chunk ** 2))

            if volume > SILENCE_THRESHOLD:
                if not is_speaking:
                    print("🗣️ ...", end="\r")  # Visual feedback
                    is_speaking = True
                audio_buffer.append(chunk)
                last_speech_time = time.time()
            else:
                if is_speaking:
                    # Abhi chup hua hai, thoda buffer aur lo
                    audio_buffer.append(chunk)

                    # Agar 1 sec se zyada chup hai -> Transcribe
                    if (time.time() - last_speech_time) > SILENCE_DURATION:
                        print("\n📝 Transcribing...", end="\r")

                        full_audio = np.concatenate(audio_buffer)

                        # Transcribe Call
                        result = model.transcribe(
                            full_audio,
                            fp16=False,
                            initial_prompt="User conversation with AI assistant."
                        )

                        text = result['text'].strip()
                        if text:
                            print(f"\n✨ User Said: {text}")
                            # Yahan aap LLM ko call kar sakte hain:
                            # llm.chat(text)

                        # Reset
                        is_speaking = False
                        audio_buffer = []
                        print("👂 Listening...", end="\r")

        except Exception as e:
            print(f"Audio Error: {e}")
            break


# MAIN THREAD (VIDEO)
def main():
    # 1. Audio Thread Start karo
    t = threading.Thread(target=audio_listener)
    t.daemon = True  # Jab Main program band ho, ye bhi band ho jaye
    t.start()

    # 2. Video Socket Setup
    context = zmq.Context()
    socket_video = context.socket(zmq.SUB)
    socket_video.connect(f"tcp://localhost:{VIDEO_PORT}")
    socket_video.setsockopt_string(zmq.SUBSCRIBE, '')

    print(f"📷 Video Receiver started on {VIDEO_PORT}...")

    while True:
        try:
            # Video Packet receive (NOBLOCK taaki hang na ho agar frame late aaye)
            try:
                packet = socket_video.recv(flags=zmq.NOBLOCK)
            except zmq.Again:
                continue  # Agar frame nahi aaya, to loop ghumaate raho

            # Decoding Logic
            np_arr = np.frombuffer(packet, dtype=np.uint8)
            frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)

            if frame is not None:
                cv.imshow("TRINETRA VISION (Video)", frame)

            if cv.waitKey(1) == ord('q'):
                break

        except Exception as e:
            print("Video Error:", e)

    cv.destroyAllWindows()


if __name__ == "__main__":
    main()