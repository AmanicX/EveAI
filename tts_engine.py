import asyncio
import edge_tts
import tempfile
import os
import time
import pygame


class ReinaTTS:
    def __init__(self, voice="en-IE-EmilyNeural"):
        self.voice = voice
        self._pygame_ready = False

    def _init_audio(self):
        if not self._pygame_ready:
            pygame.mixer.init()
            self._pygame_ready = True

    async def _generate(self, text, output_path):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate="-1%",
            pitch="+2Hz",
        )
        await communicate.save(output_path)

    def speak(self, text):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = temp_file.name
        temp_file.close()

        asyncio.run(self._generate(text, output_path))

        self._init_audio()

        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass

        try:
            os.remove(output_path)
        except Exception:
            pass

        return output_path