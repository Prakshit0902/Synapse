from faster_whisper import WhisperModel
import speech_recognition as sr
import numpy as np
import time
import colorama

import os
import sys

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

        user_home = os.path.expanduser("~")
        hf_cache_dir = os.path.join(user_home, ".cache", "huggingface", "hub")

        # Smart Check: Agar hub folder hai, aur usme kisi bhi folder ke naam mein "whisper" hai
        local_model_exists = False
        if os.path.exists(hf_cache_dir):
            for folder_name in os.listdir(hf_cache_dir):
                if "whisper" in folder_name.lower():
                    local_model_exists = True
                    break

        try:
            if not local_model_exists:
                print(colorama.Fore.YELLOW + "⚠️ AI Models not found on this PC.")
                print(
                    colorama.Fore.YELLOW + "⏳ First boot detected. Downloading official models (~1.5 GB)... Please keep internet ON and do not close the app.")
            else:
                print(colorama.Fore.CYAN + "[STT] Local Whisper models found in cache. Booting offline...")

            start_time = time.time()
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print(colorama.Fore.GREEN + f"✅ [STT] Model loaded successfully in {time.time() - start_time:.2f} seconds")

        except Exception as e:
            print(
                colorama.Fore.RED + f"[Failed] to load or download models. Please check your internet connection for the first boot!")
            print(colorama.Fore.RED + f"Error Details: {e}")
            self.model = None

      
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.2
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True

    def listen(self):
        from python.engine.tts_engine_kaggle import TTS_Engine
        while TTS_Engine._is_speaking:
            time.sleep(0.05)
        time.sleep(0.5)

# -------------------------------------
# OLD WORKING CODE (MICROPHONE INPUT)
# -------------------------------------
#         with sr.Microphone() as source:
#         # Noise adjust
#             self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
#             print(colorama.Fore.YELLOW + "\n[Listening]...", end="", flush=True)
#             broadcast_state("state", {"status": "listening"})
# 
#             try:
#                 # Sunna shuru karo
#                 audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=None)
#                 start_time = time.perf_counter()
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
#                     "thank you for watching"
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
#                     end_time = time.perf_counter()
#                     processing_time = (end_time - start_time) * 1000
#                     print(colorama.Fore.BLUE + f"[STT Processing Time]: {processing_time:.2f} ms")
#                     return audio, text.strip()
#                 else:
#                     return None, ""
# 
#             except sr.WaitTimeoutError:
#                 return None, ""
#             except Exception as e:
#                 print(colorama.Fore.RED + f"\nError: {e}")
#                 return None, ""
# -------------------------------------

        audio_input = os.environ.get("SYNAPSE_AUDIO_INPUT")
        if audio_input and os.path.exists(audio_input):
            print(colorama.Fore.CYAN + f"\n[STT] Reading audio input file: {audio_input}")
            # Clear it so we don't process it repeatedly in the next iteration
            os.environ.pop("SYNAPSE_AUDIO_INPUT", None)
            try:
                with sr.AudioFile(audio_input) as source:
                    audio = self.recognizer.record(source)
                    return self._process_audio_data(audio)
            except Exception as e:
                print(colorama.Fore.RED + f"[STT] Error reading audio file: {e}")
                return None, ""

        try:
            with sr.Microphone() as source:
                # Noise adjust
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(colorama.Fore.YELLOW + "\n[Listening]...", end="", flush=True)
                broadcast_state("state", {"status": "listening"})

                # Sunna shuru karo
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=None)
                return self._process_audio_data(audio)
        except Exception as e:
            # Fallback to console text input if mic is missing (headless environment / Kaggle)
            print(colorama.Fore.YELLOW + f"\n[STT] Microphone not available or failed: {e}")
            print(colorama.Fore.CYAN + "⌨️ Falling back to console text input...")
            try:
                text = input("User: ")
                return None, text.strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                sys.exit(0)

    def _process_audio_data(self, audio):
        if audio is None:
            return None, ""
        try:
            start_time = time.perf_counter()
            # Raw Audio Processing (Fastest Method)
            raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe (Updated with Language Constraints)
            segments, info = self.model.transcribe(
                audio_np,
                beam_size=5,
                temperature=0.0,
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
        except Exception as e:
            print(colorama.Fore.RED + f"\nError processing audio data: {e}")
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

        # Agar model load hi nahi hua (No internet on first boot), to aage mat badho
        if engine.model is None:
            print(colorama.Fore.RED + "Cannot start testing because model failed to load.")
            exit(1)

        while True:
            # Bug 1 Fix: audio aur text dono ko capture karo
            audio, text = engine.listen()

            # Agar text khali nahi hai
            if text:
                print(colorama.Fore.GREEN + f"\nUser Said: {text}")

                # Bug 2 Fix: engine.check_exit() call karna padega
                if engine.check_exit(text):
                    print(colorama.Fore.YELLOW + "Exiting...")
                    break

    except KeyboardInterrupt:
        print(colorama.Fore.YELLOW + "\nStopped by User")
