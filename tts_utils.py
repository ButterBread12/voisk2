from google.cloud import texttospeech
import pygame
import tempfile
import time
import os

# Google Cloud TTS 클라이언트 설정
client = texttospeech.TextToSpeechClient()

def speak(text):
    # 텍스트 입력 설정
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # 음성 설정 (한국어, 여성 목소리)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Wavenet-A",  # 여기서 목소리 설정을 변경할 수 있습니다.
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    # 오디오 출력 설정 (MP3 형식)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    # 텍스트를 음성으로 변환
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    # 임시 파일에 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        fp.write(response.audio_content)
        temp_file_path = fp.name
    
    # 파일 재생
    pygame.mixer.init()
    pygame.mixer.music.load(temp_file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # 음악 재생이 끝날 때까지 대기
        time.sleep(1)
    
    # pygame 종료
    pygame.mixer.quit()
    
    # 파일 사용 후 삭제
    os.remove(temp_file_path)


