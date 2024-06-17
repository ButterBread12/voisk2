import io
import os
import time
import psycopg2
from google.cloud import speech, texttospeech, dialogflow
from konlpy.tag import Okt
from playsound import playsound
from tts_utils import speak

class Bot:
    def __init__(self, credentials_path, audio_file_path, db_config):
        # Google Cloud 서비스 계정 키 파일 경로 설정
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        # Google Cloud Speech-to-Text 클라이언트 초기화
        self.speech_client = speech.SpeechClient()
        # Google Cloud Text-to-Speech 클라이언트 초기화
        self.tts_client = texttospeech.TextToSpeechClient()
        # 오디오 파일 경로 설정
        self.file_name = os.path.join(os.path.dirname(__file__), audio_file_path)
        # KoNLPy의 Okt 형태소 분석기 초기화
        self.okt = Okt()

        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()

    def load_audio(self):
        # 오디오 파일을 읽어서 음성 인식용 데이터로 설정
        with io.open(self.file_name, 'rb') as audio_file:
            content = audio_file.read()
            self.audio = speech.RecognitionAudio(content=content)

    def recognize_speech(self):
        # 음성 인식 설정 구성
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            audio_channel_count=1,
            language_code='ko-KR'
        )
        # 음성 인식 수행
        self.response = self.speech_client.recognize(config=config, audio=self.audio)

    def preprocess_text(self):
        # 음성 인식 결과 처리
        for result in self.response.results:
            transcript = result.alternatives[0].transcript  # 인식된 텍스트 추출
            cleaned_transcript = transcript.lower().strip()  # 텍스트를 소문자로 변환하고 공백 제거
            tokens = self.okt.morphs(cleaned_transcript)  # 형태소 분석을 통해 토큰화
            stop_words = set(['그리고', '그러나', '또는'])  # 불용어 집합 정의
            filtered_tokens = [word for word in tokens if word not in stop_words]  # 불용어 제거
            print('원본 텍스트: {}'.format(transcript))
            print('전처리 및 토큰화 결과: {}'.format(filtered_tokens))
            print('\n')
            self.transcript = transcript  # 전처리된 텍스트 저장

    def detect_intent_texts(self, project_id, session_id, language_code):
        # Dialogflow 세션 클라이언트 초기화
        session_client = dialogflow.SessionsClient()
        # 세션 경로 설정
        session = session_client.session_path(project_id, session_id)
        # 텍스트 입력 구성
        text_input = dialogflow.TextInput(text=self.transcript, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        # Dialogflow 인텐트 감지 요청
        response = session_client.detect_intent(session=session, query_input=query_input)

        # Text-to-Speech 요청을 위한 입력 구성
        synthesis_input = texttospeech.SynthesisInput(text=response.query_result.fulfillment_text)
        # 음성 설정
        voice = texttospeech.VoiceSelectionParams(language_code='ko-KR', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        # 오디오 설정
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        # Text-to-Speech 요청
        tts_response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        # 기존에 존재하는 응답 파일 삭제
        if os.path.exists('response2.mp3'):
            os.remove('response2.mp3')

        # 응답 오디오 파일 저장
        with io.open('response2.mp3', 'wb') as audio_file:
            audio_file.write(tts_response.audio_content)
            print('Dialogflow 응답을 "response2.mp3" 파일로 저장했습니다.\n')
           

        # 저장된 오디오 파일 재생
        playsound('response2.mp3')
        print('오디오 재생이 완료되었습니다.')

        return response

    

    def save_parameters_to_db(self, response):

        # intent_name = response.query_result.intent.display_name
        # print(f"Detected Intent: {intent_name}")

        parameters = response.query_result.parameters
        print("Detected Parameters:")

        # 파라미터 수집
        collected_params = {}
        for key, value in parameters.items():
            if key and value:  # key와 value가 존재하는지 확인
                print(f"{key}: {value}")
                collected_params[key] = str(value)
        
        if not collected_params:
            print("No valid parameters found to save.")
            return

        # 테이블 삭제 후 다시 생성
        self.cur.execute("DROP TABLE IF EXISTS hambuger")
        self.cur.execute("""
            CREATE TABLE hambuger (
                id SERIAL PRIMARY KEY
            )
        """)

        # 테이블에 존재하는 기본 컬럼 확인 (id)
        self.cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='hambuger'")
        existing_columns = [row[0] for row in self.cur.fetchall()]

        # 새로운 컬럼 생성
        for key in collected_params.keys():
            if key not in existing_columns:
                alter_table_query = f"ALTER TABLE hambuger ADD COLUMN {key} CHARACTER(255)"
                self.cur.execute(alter_table_query)

        # 동적 컬럼 및 값 설정
        columns = ', '.join(collected_params.keys())
        values = ', '.join(['%s'] * len(collected_params))
        insert_query = f"INSERT INTO hambuger ({columns}) VALUES ({values})"

        # 컬럼 값 튜플 생성
        insert_values = tuple(collected_params.values())

        # 새로운 값을 삽입
        self.cur.execute(insert_query, insert_values)

        # 변경 사항 커밋
        self.conn.commit()
    
    def check_parameters_to_db(self, response):
        # 응답에서 인텐트 이름을 가져와서 처리
        intent_name = response.query_result.intent.display_name
        print(intent_name)
        if '매장' in intent_name:
            time.sleep(5)  # 5초간 딜레이
            speak("감사합니다. 대기번호를 확인해주세요.")
            return True
        return False

    def close_db_connection(self):
        self.cur.close()
        self.conn.close()

    