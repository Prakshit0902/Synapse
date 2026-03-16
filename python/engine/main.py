import pyaudio
import pygame

from python.engine.assistant_state_manager import AssistantState
from python.engine.music_engine import MusicEngine
from python.engine.weather_system import Wheather_Engine
from python.engine.stt_engine import STT_Engine
from python.engine.tts_engine import TTS_Engine
from python.engine.llm_engine import LLM_Engine

import os

import threading
import numpy as np

from openwakeword import Model

from python.engine.vision_pro import Vision_Pro
import colorama
import time

colorama.init(autoreset=True)


class Synapse:
    def __init__(self):
        print(colorama.Fore.CYAN + f"Initializing Synapse AI Engine...")

        self.vision = Vision_Pro()
        self.mouth = TTS_Engine()
        self.ear = STT_Engine()
        self.music = MusicEngine()  # Create ONCE
        self.weather = Wheather_Engine()
        
        # Pass the music engine to brain
        self.brain = LLM_Engine(music_engine=self.music, vision_engine=self.vision)  # SHARE the same instance
        
        self.MIC_INDEX = 1
        self.manual_music_mode = False
        models_path = r"E:\MyProjects\CPP\Trinetra_Vision\src\hey_jarvis.onnx"
        self.model = Model(wakeword_models=[models_path])
        self.mouth.speak("Hi there")

    def check_exit(self, text):
        if any(word in text for word in ["music", "song", "gana", "playing"]):
            return False
        exit_phrases = ["exit", "quit", "stop", "terminate", "bye", "adios", "chal thik hai", "milte hai"]
        if any(phrase in text.lower() for phrase in exit_phrases):
            return True
        return False

    def start(self):


        # ... baki imports ...
        state_manager = AssistantState(music_engine=self.music)
        while True:
            try:
                command = None  # Har baar reset karo
                audio = None

                #  STEP 1: STATUS CHECK 
                hardware_status = self.music.check_status()

                # Agar hardware bajne laga, to manual flag hata do (Auto-sync)
                if hardware_status:
                    self.manual_music_mode = False

                # Decision: Kya Music Mode chalana hai?
                is_music_mode = hardware_status or self.manual_music_mode

                #  STEP 2: LISTENING MODES 

                # MODE A: MUSIC PLAYING (Wake Word)
                if is_music_mode:
                    if not hasattr(self, 'stream_music_mode'):
                        import pyaudio
                        self.p_audio = pyaudio.PyAudio()
                        self.stream_music_mode = self.p_audio.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            frames_per_buffer=1280,
                            input_device_index= self.MIC_INDEX
                        )

                    try:
                        # 1. Read Audio Chunk
                        raw_audio = self.stream_music_mode.read(1280, exception_on_overflow=False)
                        audio_np = np.frombuffer(raw_audio, dtype=np.int16)

                        # 2. Predict
                        prediction = self.model.predict(audio_np)

                        # 3. Key Matching
                        max_score = 0.0
                        for key, score in prediction.items():
                            if "jarvis" in key.lower() or "naina" in key.lower():
                                max_score = score
                                break

                        # 4. Action
                        if max_score > 0.5:
                            print(f"🚨 Wake Word Detected! (Score: {max_score:.2f})")

                            try:
                                pygame.mixer.music.set_volume(0.1)  # Direct 0.1 bhejo
                            except:
                                pass

                            # CRITICAL: Mic Free Karo
                            self.stream_music_mode.stop_stream()
                            self.stream_music_mode.close()
                            self.p_audio.terminate()
                            del self.stream_music_mode
                            del self.p_audio

                            time.sleep(0.5)

                            # Google Listen
                            print("👂 Listening for command...")
                            try:
                                _, command = self.ear.listen()
                            except Exception as e:
                                command = None

                            self.music.restore_volume()

                            # Agar command nahi mili to wapas loop me
                            if not command:
                                continue

                        else:
                            continue  # Wake word nahi mila, loop continue

                    except Exception as e:
                        continue

                # MODE B: NORMAL LISTENING (Jab Music Band Ho)


                else:
                    # Cleanup: Agar galti se stream khuli reh gayi
                    if hasattr(self, 'stream_music_mode'):
                        try:
                            self.stream_music_mode.close()
                            self.p_audio.terminate()
                            del self.stream_music_mode
                            del self.p_audio
                        except:
                            pass

                    # Normal Listen
                    try:
                        audio, command = self.ear.listen()
                    except:
                        command = None

                #  STEP 3: PROCESSING PHASE 

                if command:
                    print(f"🎤 Heard: {command}")
                    command_lower = command.lower()

                    # 1. EXIT CHECK
                    if self.check_exit(command_lower):
                        self.vision.close_camera()
                        self.mouth.speak("Goodbye!")
                        print("Stopping Synapse...")
                        os._exit(0)

                    # 2. Use ONLY the agentic approach for everything
                    print(f"🤖 Processing with Agent: {command}")
                    agentic_response = self.brain.run_agentic_llm(command)
                    if agentic_response and "[REGISTER]" in agentic_response:
                        # Parse the signal: "[REGISTER] Ankit | DSA King"
                        try:
                            clean_data = agentic_response.replace("[REGISTER]", "").strip()
                            name_part, info_part = clean_data.split("|", 1)

                            print(f"🚀 Triggering Registration for: {name_part.strip()}")
                            self.handle_registration_flow(pre_name=name_part.strip(), pre_info=info_part.strip())
                            continue  # Loop wapas start karo
                        except Exception as e:
                            print(f"Registration Parse Error: {e}")
                            self.mouth.speak("I had trouble starting the registration.")

                    if agentic_response and "I encountered" not in agentic_response:
                        print(f"🤖 Agent Response: {agentic_response}")

                        # Check if it's a music response - DON'T speak it
                        if "Starting music:" in agentic_response:
                            print("[System] Music starting - Skipping TTS to avoid conflict")
                            self.manual_music_mode = True
                            time.sleep(2)  # Wait for music to start
                        else:
                            # Only speak non-music responses
                            self.mouth.speak(agentic_response)

                        continue

                    # Fallback to chat if agent fails
                    print(f"💬 Falling back to Chat: {command}")
                    ai_response = self.brain.chat(command)
                    self.mouth.speak(ai_response)

            except KeyboardInterrupt:
                print("\nStopping Synapse...")
                break
            except Exception as e:
                print(f"Critical Error in Main Loop: {e}")
                time.sleep(1)

    # def handle_registration_flow(self, auto_trigger=False, pre_name=None, pre_info=None):
    #     """
    #     Handles registration flow.
    #     - Supports Auto-trigger (When unknown face is seen)
    #     - Supports Agent-trigger (When user says 'Register Ankit')
    #     """
    #
    #     # Initialize variables from Agent arguments (if any)
    #     final_name = pre_name
    #     final_info = pre_info if pre_info else ""
    #
    #     def wait_for_sarah():
    #         """Helper to pause execution while TTS is speaking"""
    #         time.sleep(0.5)
    #         # Safe check in case mouth is busy
    #         while hasattr(self.mouth, '_is_speaking') and self.mouth._is_speaking:
    #             time.sleep(0.1)
    #
    #     #  CASE 1: AUTO TRIGGER (Unknown Face Detected) 
    #     # Sirf tab chalega jab auto_trigger True ho aur Agent ne naam na diya ho
    #     if auto_trigger and not final_name:
    #         self.mouth.speak("I see someone new. Do you want me to remember them?")
    #         wait_for_sarah()
    #
    #         print("[System] Waiting for User Decision (Yes/No)...")
    #         decision_made = False
    #
    #         # 3 Attempts denge user ko jawab dene ke liye
    #         for _ in range(3):
    #             response = self.ear.listen()
    #             if not response: continue
    #
    #             if any(w in response.lower() for w in ["yes", "haan", "yep", "sure", "ok"]):
    #                 decision_made = True
    #                 break
    #             elif any(w in response.lower() for w in ["no", "nah", "nahi", "cancel"]):
    #                 self.mouth.speak("Okay, ignoring.")
    #                 return  # Exit function
    #
    #         if not decision_made:
    #             self.mouth.speak("No response. Ignoring for now.")
    #             return
    #
    #     #  CASE 2: NAME GATHERING (Only if Agent/Auto didn't give a name) 
    #     if not final_name:
    #         self.mouth.speak("Okay, tell me their name.")
    #         wait_for_sarah()
    #
    #         attempts = 0
    #         while attempts < 3:
    #             print(f"[System] Listening for Name (Attempt {attempts + 1})...")
    #             user_input = self.ear.listen()
    #
    #             if not user_input:
    #                 self.mouth.speak("I didn't hear anything. Please say the name.")
    #                 wait_for_sarah()
    #                 continue
    #
    #             if "cancel" in user_input.lower():
    #                 self.mouth.speak("Registration cancelled.")
    #                 return
    #
    #             # Brain processing (Your original logic to clean name)
    #             person_data = self.brain.process_name_info(user_input)
    #             extracted_name = person_data.get("name", user_input)
    #             temp_info = person_data.get("info", "")
    #
    #             if extracted_name == "Unknown":
    #                 self.mouth.speak("I couldn't understand the name. Please try again.")
    #                 wait_for_sarah()
    #                 continue
    #
    #             # Smart Confirmation
    #             self.mouth.speak(f"I heard {extracted_name}. Is that correct?")
    #             wait_for_sarah()
    #             confirm = self.ear.listen()
    #
    #             if confirm and any(w in confirm.lower() for w in ["yes", "haan", "sahi", "right", "correct"]):
    #                 final_name = extracted_name
    #                 if len(temp_info) > 2:
    #                     final_info = temp_info
    #                 break
    #             else:
    #                 self.mouth.speak("Sorry. Please say the name again.")
    #                 wait_for_sarah()
    #
    #             attempts += 1
    #
    #     # Check if we still don't have a name after loops
    #     if not final_name:
    #         self.mouth.speak("I am struggling to hear. Let's try later.")
    #         return
    #
    #     #  STEP 3: EXISTING USER CHECK 
    #     # Vision engine check: Kya ye naam pehle se DB me hai?
    #     existing_info = self.vision.check_person_exists(final_name)
    #
    #     if existing_info:
    #         current_details = existing_info.get("details", "No details provided")
    #         self.mouth.speak(f"Wait, I already know {final_name}. You told me: {current_details}.")
    #         wait_for_sarah()
    #         self.mouth.speak("Do you want to update this information?")
    #         wait_for_sarah()
    #
    #         update_response = self.ear.listen()
    #
    #         if update_response and any(w in update_response.lower() for w in ["yes", "haan", "update", "change"]):
    #             # If Agent provided new info, use it directly
    #             if pre_info and len(pre_info) > 5:
    #                 new_details = pre_info
    #             else:
    #                 self.mouth.speak(f"Okay, tell me, who is {final_name} now?")
    #                 wait_for_sarah()
    #                 new_details = self.ear.listen()
    #
    #             if new_details:
    #                 new_info_dict = {"details": new_details, "added_on": time.strftime("%Y-%m-%d"), "updated": True}
    #                 if self.vision.update_person_info(final_name, new_info_dict):
    #                     self.mouth.speak(f"Done. I have updated the information for {final_name}.")
    #                 else:
    #                     self.mouth.speak("Failed to update database.")
    #             else:
    #                 self.mouth.speak("I didn't hear anything. Keeping old info.")
    #         else:
    #             self.mouth.speak("Okay, keeping the existing information.")
    #
    #         return  # Exit, no photo needed for update
    #
    #     #  STEP 4: MANDATORY INFO (Only if info is missing) 
    #     if len(final_info) < 5:
    #         self.mouth.speak(f"Got it, {final_name}. Now, tell me, who is he? What do you want me to remember?")
    #         wait_for_sarah()
    #
    #         details_input = self.ear.listen()
    #         if details_input and len(details_input) > 2:
    #             final_info = details_input
    #         else:
    #             final_info = "Just a friend."
    #             self.mouth.speak("Okay, I'll just remember him as a friend.")
    #             wait_for_sarah()
    #
    #     #  STEP 5: VISION REGISTRATION (Photo Session) 
    #     self.mouth.speak(f"Registering {final_name}. Please look at the camera.")
    #     wait_for_sarah()
    #
    #     # Use the vision object from self (Shared object)
    #     # Note: Hum naya frame read kar rahe hain taaki latest pose capture ho
    #     ret, frame = self.vision.cap.read()
    #     if ret:
    #         info_dict = {"details": final_info, "added_on": time.strftime("%Y-%m-%d")}
    #
    #         # Pass 'self.mouth' so Vision can give voice instructions (Left/Right turn etc.)
    #         success = self.vision.register_face(frame, final_name, info_dict, self.mouth)
    #
    #         if not success:
    #             self.mouth.speak("Face capture failed.")
    #     else:
    #         self.mouth.speak("Camera error.")


if __name__ == "__main__":
    try:
        app = Synapse()
        app.start()
    except KeyboardInterrupt:
        print(f"Interrupted by user")