import numpy as np
from scipy.io.wavfile import write
from pydub import AudioSegment
import time


# 샘플링 레이트 설정 (Hz)
fs = 44100

# 오디오 콜백 함수
def audio_callback(indata, frames, time_param, status, threshold, silent_blocks, max_silent_blocks, recording, recorded_frames, start_time, speak, stop_stream):
    # 입력된 오디오 데이터의 볼륨 계산 (정규화)
    volume_norm = np.linalg.norm(indata) * 10
    print(f'Volume: {volume_norm}')

    # 볼륨이 임계값보다 작은 경우 (무음 감지)
    if volume_norm < threshold:
        # 현재 녹음 중이라면
        if recording[0]:
            silent_blocks[0] += 1
            # 최대 무음 블록 수를 초과하면 녹음 종료
            if silent_blocks[0] > max_silent_blocks:
                print("무음 감지로 인해 녹음이 종료되었습니다.")
                save_recording(recorded_frames, fs)  # 녹음된 데이터를 저장
                stop_stream[0] = True  # 스트림 중단 신호 설정
        else:
            curr_time = time.time()
            if int(curr_time - start_time) >= 10 and int(curr_time - start_time) % 10 == 0:
                print("주문해주세요.")
                speak("주문해주세요.")
    else:
        silent_blocks[0] = 0
        # 녹음이 시작되지 않은 경우, 녹음 시작
        if not recording[0]:
            print("녹음이 시작되었습니다.")
            recording[0] = True
            start_time = time.time()

    # 녹음 중이라면, 녹음된 프레임 저장
    if recording[0]:
        recorded_frames.append(indata.copy())

# 녹음된 데이터를 파일로 저장하는 함수
def save_recording(recorded_frames, fs):
    print("녹음이 완료되었습니다.")
    if recorded_frames:
        # 녹음된 프레임들을 하나로 연결
        myrecording = np.concatenate(recorded_frames, axis=0)
        
        # 증폭 계수 설정
        gain = 2.0
        
        # 녹음 데이터를 증폭
        myrecording_amplified = myrecording * gain
        
        # 데이터 값을 클리핑하여 [-1.0, 1.0] 범위로 제한
        myrecording_amplified = np.clip(myrecording_amplified, -1.0, 1.0)
        
        # 16비트 정수형으로 변환
        myrecording_amplified = (myrecording_amplified * np.iinfo(np.int16).max).astype(np.int16)
        
        # WAV 파일로 저장
        wav_file = 'cjsrhkdgus1.wav'
        write(wav_file, fs, myrecording_amplified)
        
        # WAV 파일을 MP3 파일로 변환
        audio = AudioSegment.from_wav(wav_file)
        audio.export("cjsrhkdgus1.mp3", format="mp3")
        print("MP3 파일로 변환되어 저장되었습니다.")
