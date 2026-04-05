# from faster_whisper import WhisperModel
# import speech_recognition as sr
# import numpy as np
# import time
# import colorama
#
# # Colors init
# colorama.init(autoreset=True)
#
#
# class STT_Engine:
#     def __init__(self):
#         print(colorama.Fore.CYAN + "[STT] Initializing Whisper Model...")
#
#         # Configuration
#         # self.mic_index = 9
#         model_size = "distil-large-v3"
#         device = "cuda"  # Agar error aaye to "cpu" kar dena
#         compute_type = "int8"  # CPU ke liye "int8" use karna
#
#         start_time = time.time()
#         self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
#         print(colorama.Fore.GREEN + f"[STT] Model loaded in {time.time() - start_time:.2f} seconds")
#
#         self.recognizer = sr.Recognizer()
#         self.recognizer.pause_threshold = 1.2
#         self.recognizer.energy_threshold = 3000
#         self.recognizer.dynamic_energy_threshold = False
#
#
#
#     def listen(self):
#         time.sleep(0.5)
#         with sr.Microphone() as source:
#             # Noise adjust
#             self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
#
#             print(colorama.Fore.YELLOW + "\n[Listening]...", end="", flush=True)
#
#             try:
#                 # Sunna shuru karo
#                 audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=None)
#
#                 # Raw Audio Processing (Fastest Method)
#                 raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
#                 audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
#
#                 # Transcribe
#                 # Transcribe (Updated with Language Constraints)
#                 segments, info = self.model.transcribe(
#                     audio_np,
#                     beam_size=5,
#                     # 1. Ye prompt model ko batata hai ki Hinglish expect kare
#                     # initial_prompt="Priyadarshan, Trinetra, Jarvis, Ankit, Prerak,Dandotia, Hindi, English, Code, Python",
#                     # 2. Temperature 0 karne se wo creative nahi banta (Hallucination kam hoti hai)
#                     temperature=0.0,
#                     # 3. Pichli baat se confuse na ho (Commands ke liye acha hai)
#                     condition_on_previous_text=False
#                 )
#                 text = " ".join([segment.text for segment in segments])
#                 hallucinations = [
#                     "thank you", "thanks", "you", "watching", "subtitles",
#                     "copyright", "audio", "bye", "amara", "org",
#                     "the user speaks in hinglish",  # YE HAI CULPRIT
#                     "user speaks in hinglish",
#                     "thank you for watching",
#                     "thank you thank you."
#                 ]
#                 # Agar text sirf hallucination hai -> Ignore
#                 # (e.g., Sirf "Thank you." aaya to ignore, par "Thank you Jarvis" aaya to chalega)
#                 clean_text = text.lower().replace(".", "").strip()
#                 if clean_text in hallucinations:
#                     print(f"🚫 Ignored Hallucination: '{text}'")
#                     return None, ""
#                 if len(clean_text.split()) > 3 and len(set(clean_text.split())) == 1:
#                     print(f"🚫 Ignored Repetitive Loop: '{text}'")
#                     return None, ""
#
#                 if "hindi" in clean_text and len(clean_text) < 10:
#                     return None, ""
#
#                 if text.strip():
#                     return audio, text.strip()
#                 else:
#                     return None, ""
#
#             except sr.WaitTimeoutError as e:
#                 print(e)
#                 print(
#                     "[Debug] : Timeout Error. Retrying... (If this continues, please check your microphone connection)")
#                 return None, ""
#             except Exception as e:
#                 print(colorama.Fore.RED + f"\nError: {e}")
#                 return None, ""
#
#
# # Ye helper function class ke bahar hi thik hai
# # This method is just for checking purpose I already have this method in main.py
# def check_exit(text):
#     if not text:
#         return False
#     exit_phrases = ["exit", "quit", "stop", "terminate", "bye", "adios"]
#     if any(phrase in text.lower() for phrase in exit_phrases):
#         return True
#     return False
#
#
# # Testing Code (Sirf tab chalega jab is file ko directly run karoge)
# if __name__ == "__main__":
#     try:
#         # Class ka object banao
#         engine = STT_Engine()
#
#         while True:
#             # Object ka function call karo
#             text = engine.listen()
#
#             if text:
#                 print(f"\nUser Said: {text}")
#                 if check_exit(text):
#                     print("Exiting...")
#                     break
#     except KeyboardInterrupt:
#         print("\nStopped by User")


from faster_whisper import WhisperModel
import speech_recognition as sr
import numpy as np
import time
import colorama



from python.engine.event_bus import broadcast_state

# Colors init
colorama.init(autoreset=True)


class STT_Engine:
    def __init__(self):
        print(colorama.Fore.CYAN + "[STT] Initializing Whisper Model...")

        # Configuration
        model_size = "distil-large-v3"
        device = "cuda"  # Agar error aaye to "cpu" kar dena
        compute_type = "int8"  # CPU ke liye "int8" use karna

        start_time = time.time()
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(colorama.Fore.GREEN + f"[STT] Model loaded in {time.time() - start_time:.2f} seconds")

        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.2
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True

    def listen(self):
        from tts_engine import TTS_Engine
        while TTS_Engine._is_speaking:
            time.sleep(0.05)
        time.sleep(0.5)

        with sr.Microphone() as source:
        # Noise adjust
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(colorama.Fore.YELLOW + "\n[Listening]...", end="", flush=True)
            broadcast_state("state", {"state":"listening"})

            try:
                # Sunna shuru karo
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=None)
                start_time = time.perf_counter()

                # Raw Audio Processing (Fastest Method)
                raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Transcribe
                # Transcribe (Updated with Language Constraints)
                segments, info = self.model.transcribe(
                    audio_np,
                    beam_size=5,
                    # 1. Ye prompt model ko batata hai ki Hinglish expect kare
                    # initial_prompt="Priyadarshan, Trinetra, Jarvis, Ankit, Prerak,Dandotia, Hindi, English, Code, Python",
                    # 2. Temperature 0 karne se wo creative nahi banta (Hallucination kam hoti hai)
                    temperature=0.0,
                    # 3. Pichli baat se confuse na ho (Commands ke liye acha hai)
                    condition_on_previous_text=False
                )
                text = " ".join([segment.text for segment in segments])
                hallucinations = [
                    "thank you", "thanks", "you", "watching", "subtitles",
                    "copyright", "audio", "bye", "amara", "org",
                    "the user speaks in hinglish",  # YE HAI CULPRIT
                    "user speaks in hinglish",
                    "thank you for watching"
                ]
                # Agar text sirf hallucination hai -> Ignore
                # (e.g., Sirf "Thank you." aaya to ignore, par "Thank you Jarvis" aaya to chalega)
                clean_text = text.lower().replace(".", "").strip()
                if clean_text in hallucinations:
                    print(f"🚫 Ignored Hallucination: '{text}'")
                    return None, ""
                if len(clean_text.split()) > 3 and len(set(clean_text.split())) == 1:
                    print(f"🚫 Ignored Repetitive Loop: '{text}'")
                    return None, ""

                if "hindi" in clean_text and len(clean_text) < 10:
                    return None, ""

                if text.strip():
                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000
                    print(colorama.Fore.BLUE + f"[STT Processing Time]: {processing_time:.2f} ms")
                    return audio, text.strip()
                else:
                    return None, ""

            except sr.WaitTimeoutError:
                return None, ""
            except Exception as e:
                print(colorama.Fore.RED + f"\nError: {e}")
                return None, ""


# Ye helper function class ke bahar hi thik hai
# This method is just for checking purpose I already have this method in main.py
    def check_exit(self,text):
        if not text:
            return False
        exit_phrases = ["exit", "quit", "stop", "terminate", "bye", "adios"]
        if any(phrase in text.lower() for phrase in exit_phrases):
            return True
        return False

    def transcribe_raw(self, audio_np):
            """
                Takes raw audio data from ZeroMQ socket and transcribes it using CUDA-accelerated Whisper.

                Args:
                    audio_data (bytes): Raw byte stream from the Raspberry Pi microphone.
                    model_name (str, optional): The speech-to-text model to use. Defaults to "whisper".

                Returns:
                    str: Transcribed text generated by the model.
                """

            try:
                # Model already RAM/VRAM me loaded hai, seedha data pass karo
                segments, info = self.model.transcribe(
                    audio_np,
                    beam_size=5,
                    temperature=0.0,
                    vad_filter=True,
                )
                text = " ".join([segment.text for segment in segments])

                # Hallucination Logic (Same as your original)
                clean_text = text.lower().replace(".", "").strip()
                hallucinations = [
                    "thank you", "thanks", "you", "watching", "subtitles",
                    "copyright", "audio", "bye", "amara", "org",
                    "the user speaks in hinglish", "user speaks in hinglish",
                    "thank you for watching",
                    "pomayor", "oh", "bas thank you",
                    "thank you thank you."
                ]

                if clean_text in hallucinations:
                    return None
                if len(clean_text.split()) > 3 and len(set(clean_text.split())) == 1:
                    return None
                if "hindi" in clean_text and len(clean_text) < 10:
                    return None

                return text.strip() if text.strip() else None

            except Exception as e:
                print(colorama.Fore.RED + f"[STT Edge Error]: {e}")
                return None

# Testing Code (Sirf tab chalega jab is file ko directly run karoge)
if __name__ == "__main__":
    try:
        # Class ka object banao
        engine = STT_Engine()

        while True:
            # Object ka function call karo
            text = engine.listen()

            if text:
                print(f"\nUser Said: {text}")
                if check_exit(text):
                    print("Exiting...")
                    break
    except KeyboardInterrupt:
        print("\nStopped by User")
