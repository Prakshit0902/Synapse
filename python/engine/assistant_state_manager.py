import time

"""
This class is for checking what Synapse is doing... Means its state 
Like Idle, Speaking,Listening.
"""

class AssistantState:
    def __init__(self, music_engine=None):
        self.music = music_engine
        self.is_speaking = False
        self.is_listening = False
        self.last_interaction = time.time()

    def set_speaking(self, status):
        """
        Update / Set speaking status.

        If speaking = True, lower the music volume.
        """
        self.is_speaking = status

        if self.music:
            if status:
                # Jab Assistant bole, music slow karo
                try:
                    import pygame
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.set_volume(0.1)
                except:
                    pass
            else:
                # Jab chup ho jaye, wapas normal karo
                self.music.restore_volume()

    def set_listening(self, status):
        self.is_listening = status
        if status:
            self.last_interaction = time.time()

    def get_state(self):
        if self.is_speaking:
            return "SPEAKING"
        elif self.is_listening:
            return "LISTENING"
        else:
            return "IDLE"