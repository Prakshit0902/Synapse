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
        state = AssistantState()
        while True:
            try:
                if TTS_Engine._is_speaking:
                    time.sleep(0.05)
                    continue

                state.set_listening(True)
                audio, command = self.ear.listen()
                state.set_listening(False)

                if command:
                    print(f"[Heard] : {command}")

                    if self.check_exit(command.lower()):
                        self.vision.close_camera()
                        self.mouth.speak("Goodbye!")
                        os._exit(0)

                    print(f"[Processing] : {command}")
                    agentic_response = self.brain.run_agentic_llm(command)

                    if agentic_response and "[REGISTER]" in agentic_response:
                        try:
                            clean_data = agentic_response.replace("[REGISTER]", "").strip()
                            name_part, info_part = clean_data.split("|", 1)
                            self.handle_registration_flow(
                                pre_name=name_part.strip(),
                                pre_info=info_part.strip()
                            )
                        except Exception as e:
                            print(f"Registration Error: {e}")
                        continue

                    if agentic_response and "I encountered" not in agentic_response:
                        print(f"[Response] : {agentic_response}")
                        self.mouth.speak(agentic_response)
                        continue

                    # Fallback
                    print(f"[Fallback Chat] : {command}")
                    ai_response = self.brain.chat(command)
                    self.mouth.speak(ai_response)

            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print(f"Critical Error: {e}")
                time.sleep(1)

    def handle_registration_flow(self, auto_trigger=False, pre_name=None, pre_info=None):
        """
        Handles registration flow.
        - Supports Auto-trigger (When unknown face is seen)
        - Supports Agent-trigger (When user says 'Register Ankit')
        """

        # Initialize variables from Agent arguments (if any)
        final_name = pre_name
        final_info = pre_info if pre_info else ""

        def wait_for_sarah():
            """Helper to pause execution while TTS is speaking"""
            time.sleep(0.5)
            # Safe check in case mouth is busy
            while hasattr(self.mouth, '_is_speaking') and self.mouth._is_speaking:
                time.sleep(0.1)

        #  AUTO TRIGGER (Unknown Face Detected)
        # Sirf tab chalega jab auto_trigger True ho aur Agent ne naam na diya ho
        if auto_trigger and not final_name:
            self.mouth.speak("I see someone new. Do you want me to remember them?")
            wait_for_sarah()

            print("[System] Waiting for User Decision (Yes/No)...")
            decision_made = False

            # 3 Attempts denge user ko jawab dene ke liye
            for _ in range(3):
                response = self.ear.listen()
                if not response: continue

                if any(w in response.lower() for w in ["yes", "haan", "yep", "sure", "ok"]):
                    decision_made = True
                    break
                elif any(w in response.lower() for w in ["no", "nah", "nahi", "cancel"]):
                    self.mouth.speak("Okay, ignoring.")
                    return  # Exit function

            if not decision_made:
                self.mouth.speak("No response. Ignoring for now.")
                return

        #  NAME GATHERING (Only if Agent/Auto didn't give a name)
        if not final_name:
            self.mouth.speak("Okay, tell me their name.")
            wait_for_sarah()

            attempts = 0
            while attempts < 3:
                print(f"[System] Listening for Name (Attempt {attempts + 1})...")
                user_input = self.ear.listen()

                if not user_input:
                    self.mouth.speak("I didn't hear anything. Please say the name.")
                    wait_for_sarah()
                    continue

                if "cancel" in user_input.lower():
                    self.mouth.speak("Registration cancelled.")
                    return

                # Brain processing (Your original logic to clean name)
                person_data = self.brain.process_name_info(user_input)
                extracted_name = person_data.get("name", user_input)
                temp_info = person_data.get("info", "")

                if extracted_name == "Unknown":
                    self.mouth.speak("I couldn't understand the name. Please try again.")
                    wait_for_sarah()
                    continue

                # Smart Confirmation
                self.mouth.speak(f"I heard {extracted_name}. Is that correct?")
                wait_for_sarah()
                confirm = self.ear.listen()

                if confirm and any(w in confirm.lower() for w in ["yes", "haan", "sahi", "right", "correct"]):
                    final_name = extracted_name
                    if len(temp_info) > 2:
                        final_info = temp_info
                    break
                else:
                    self.mouth.speak("Sorry. Please say the name again.")
                    wait_for_sarah()

                attempts += 1

        # Check if we still don't have a name after loops
        if not final_name:
            self.mouth.speak("I am struggling to hear. Let's try later.")
            return

        #   EXISTING USER CHECK
        # Vision engine check: Kya ye naam pehle se DB me hai?
        existing_info = self.vision.check_person_exists(final_name)

        if existing_info:
            current_details = existing_info.get("details", "No details provided")
            self.mouth.speak(f"Wait, I already know {final_name}. You told me: {current_details}.")
            wait_for_sarah()
            self.mouth.speak("Do you want to update this information?")
            wait_for_sarah()

            update_response = self.ear.listen()

            if update_response and any(w in update_response.lower() for w in ["yes", "haan", "update", "change"]):
                # If Agent provided new info, use it directly
                if pre_info and len(pre_info) > 5:
                    new_details = pre_info
                else:
                    self.mouth.speak(f"Okay, tell me, who is {final_name} now?")
                    wait_for_sarah()
                    new_details = self.ear.listen()

                if new_details:
                    new_info_dict = {"details": new_details, "added_on": time.strftime("%Y-%m-%d"), "updated": True}
                    if self.vision.update_person_info(final_name, new_info_dict):
                        self.mouth.speak(f"Done. I have updated the information for {final_name}.")
                    else:
                        self.mouth.speak("Failed to update database.")
                else:
                    self.mouth.speak("I didn't hear anything. Keeping old info.")
            else:
                self.mouth.speak("Okay, keeping the existing information.")

            return  # Exit, no photo needed for update

        # MANDATORY INFO (Only if info is missing)
        if len(final_info) < 5:
            self.mouth.speak(f"Got it, {final_name}. Now, tell me, who is he? What do you want me to remember?")
            wait_for_sarah()

            details_input = self.ear.listen()
            if details_input and len(details_input) > 2:
                final_info = details_input
            else:
                final_info = "Just a friend."
                self.mouth.speak("Okay, I'll just remember him as a friend.")
                wait_for_sarah()

        #   VISION REGISTRATION (Photo Session)
        self.mouth.speak(f"Registering {final_name}. Please look at the camera.")
        wait_for_sarah()

        # Use the vision object from self (Shared object)
        # Note: Hum naya frame read kar rahe hain taaki latest pose capture ho
        ret, frame = self.vision.cap.read()
        if ret:
            info_dict = {"details": final_info, "added_on": time.strftime("%Y-%m-%d")}

            # Pass 'self.mouth' so Vision can give voice instructions (Left/Right turn etc.)
            success = self.vision.register_face(frame, final_name, info_dict, self.mouth)

            if not success:
                self.mouth.speak("Face capture failed.")
        else:
            self.mouth.speak("Camera error.")


if __name__ == "__main__":
    try:
        app = Synapse()
        app.start()
    except KeyboardInterrupt:
        print(f"Interrupted by user")