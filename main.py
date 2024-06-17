import time
import sounddevice as sd
from audio_recording import audio_callback, save_recording
from tts_utils import speak
import DF_BOT_SUM2 as bot_module

fs = 44100
duration = 200
threshold = 200
block_duration = 0.1
max_silent_blocks = 20
recording = [False]
start_time = time.time()
recorded_frames = []
silent_blocks = [0]
stop_stream = [False]

def run_audio_stream():
    try:
        with sd.InputStream(callback=lambda indata, frames, time, status: audio_callback(indata, frames, time, status, threshold, silent_blocks, max_silent_blocks, recording, recorded_frames, start_time, speak, stop_stream), channels=2, samplerate=fs, blocksize=int(fs * block_duration)):
            while not stop_stream[0]:
                sd.sleep(100)
    except Exception as e:
        print(f"오류 발생: {e}")

def run_bot(db_config):
    bot = bot_module.Bot(r"C:\Users\cjsrh\OneDrive\바탕 화면\hello\my-project-1004-413005-c6a404a02fd6.json", 'cjsrhkdgus1.mp3', db_config)
    bot.load_audio()
    bot.recognize_speech()
    bot.preprocess_text()
    if bot.transcript is None:
        return False
    response = bot.detect_intent_texts('my-project-1004-413005', 'fixed_session_id', 'ko')
    bot.save_parameters_to_db(response)
    if bot.check_parameters_to_db(response):
        return True
    bot.close_db_connection()
    return False

def reset_stream_status():
    global stop_stream, recording, recorded_frames, silent_blocks, start_time
    stop_stream[0] = False
    recording[0] = False
    recorded_frames.clear()
    silent_blocks[0] = 0
    start_time = time.time()

def main_loop(db_config):
    while True:
        run_audio_stream()
        if run_bot(db_config):
            break
        reset_stream_status()
        time.sleep(1)

if __name__ == "__main__":
    db_config = {
        'dbname': 'kiosk2',
        'user': 'postgres',
        'password': '1860047',
        'host': 'localhost',
        'port': 5432,
    }
    main_loop(db_config)
