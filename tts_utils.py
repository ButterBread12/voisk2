from gtts import gTTS
import tempfile
import pygame
import time

# 텍스트를 음성으로 변환하여 재생하는 함수
def speak(text):
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        tts = gTTS(text=text, lang='ko')
        tts.save(f"{fp.name}.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load(f"{fp.name}.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # 음악 재생이 끝날 때까지 대기
            time.sleep(1)
