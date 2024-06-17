import time
import sounddevice as sd
from audio_recording import audio_callback, save_recording
from tts_utils import speak
import DF_BOT_SUM2 as bot_module

fs = 44100  # 샘플링 레이트
duration = 200  # 녹음할 총 시간 (초단위)
threshold = 50
block_duration = 0.1
max_silent_blocks = 20
recording = [False]
start_time = time.time()
recorded_frames = []
silent_blocks = [0]
stop_stream = [False]  # 스트림 중단 상태 변수

def run_audio_stream():
    try:
        with sd.InputStream(callback=lambda indata, frames, time, status: audio_callback(indata, frames, time, status, threshold, silent_blocks, max_silent_blocks, recording, recorded_frames, start_time, speak, stop_stream), channels=2, samplerate=fs, blocksize=int(fs * block_duration)):
            while not stop_stream[0]:
                sd.sleep(100)  # 짧은 주기로 스트림 상태를 감시
    except Exception as e:
        print(f"오류 발생: {e}")

def run_bot(db_config):  # 사용 예시
    bot = bot_module.Bot(r"C:\Users\cjsrh\OneDrive\바탕 화면\hello\my-project-1004-413005-c6a404a02fd6.json", 'cjsrhkdgus1.mp3', db_config)
    bot.load_audio()
    bot.recognize_speech()
    bot.preprocess_text()
    response = bot.detect_intent_texts('my-project-1004-413005', 'fixed_session_id', 'ko')
    bot.save_parameters_to_db(response)  # 파라미터를 데이터베이스에 저장
    if bot.check_parameters_to_db(response):  # '매장'이 포함된 경우 루프 종료
        return True
    bot.close_db_connection()  # 데이터베이스 연결 종료
    return False  

if __name__ == "__main__":
    db_config = {
        'dbname': 'kiosk2',
        'user': 'postgres',
        'password': '1860047',
        'host': 'localhost',
        'port': 5432,
    }

    while True:
        run_audio_stream()
        if run_bot(db_config):
            break
        # 스트림 중단 및 상태 초기화
        stop_stream = [False]
        recording = [False]
        recorded_frames = []
        silent_blocks = [0]
        start_time = time.time()
        time.sleep(1)  # 루프가 너무 빠르게 반복되지 않도록 잠시 대기
        
