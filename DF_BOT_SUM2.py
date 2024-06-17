import io
import os
import time
import psycopg2
import pygame
from google.cloud import speech, texttospeech, dialogflow
from konlpy.tag import Okt
from tts_utils import speak

class Bot:
    def __init__(self, credentials_path, audio_file_path, db_config):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.speech_client = speech.SpeechClient()
        self.tts_client = texttospeech.TextToSpeechClient()
        self.file_name = os.path.join(os.path.dirname(__file__), audio_file_path)
        self.okt = Okt()
        pygame.mixer.init()
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()

    def load_audio(self):
        with io.open(self.file_name, 'rb') as audio_file:
            content = audio_file.read()
            self.audio = speech.RecognitionAudio(content=content)

    def recognize_speech(self):
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            audio_channel_count=1,
            language_code='ko-KR'
        )
        self.response = self.speech_client.recognize(config=config, audio=self.audio)

    def preprocess_text(self):
        if not self.response.results:
            speak("다시 말해주세요잉")
            print('값이 없어용')
            self.transcript = None
            return
        for result in self.response.results:
            transcript = result.alternatives[0].transcript
            cleaned_transcript = transcript.lower().strip()
            tokens = self.okt.morphs(cleaned_transcript)
            stop_words = set(['그리고', '그러나', '또는'])
            filtered_tokens = [word for word in tokens if word not in stop_words]
            print('원본 텍스트: {}'.format(transcript))
            print('전처리 및 토큰화 결과: {}'.format(filtered_tokens))
            self.transcript = transcript

    def detect_intent_texts(self, project_id, session_id, language_code):
        if not self.transcript:
            return None
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=self.transcript, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)

        synthesis_input = texttospeech.SynthesisInput(text=response.query_result.fulfillment_text)
        voice = texttospeech.VoiceSelectionParams(language_code='ko-KR', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        tts_response = self.tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        if os.path.exists('response2.mp3'):
            os.remove('response2.mp3')

        with io.open('response2.mp3', 'wb') as audio_file:
            audio_file.write(tts_response.audio_content)
            print('Dialogflow 응답을 "response2.mp3" 파일로 저장했습니다.\n')

        pygame.mixer.music.load('response2.mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        print('오디오 재생이 완료되었습니다.')
        return response

    def save_parameters_to_db(self, response):
        if response is None:
            return
        parameters = response.query_result.parameters
        print("Detected Parameters:")
        collected_params = {key: str(value) for key, value in parameters.items() if key and value}
        if not collected_params:
            print("No valid parameters found to save.")
            return
        self.cur.execute("DROP TABLE IF EXISTS hamburger")
        self.cur.execute("""
            CREATE TABLE hamburger (
                id SERIAL PRIMARY KEY
            )
        """)
        self.cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='hamburger'")
        existing_columns = [row[0] for row in self.cur.fetchall()]
        for key in collected_params.keys():
            if key not in existing_columns:
                alter_table_query = f"ALTER TABLE hamburger ADD COLUMN {key} CHARACTER(30)"
                self.cur.execute(alter_table_query)
        columns = ', '.join(collected_params.keys())
        values = ', '.join(['%s'] * len(collected_params))
        insert_query = f"INSERT INTO hamburger ({columns}) VALUES ({values})"
        insert_values = tuple(collected_params.values())
        self.cur.execute(insert_query, insert_values)
        self.conn.commit()

    def check_parameters_to_db(self, response):
        if response is None:
            return False
        intent_name = response.query_result.intent.display_name
        print(intent_name)
        if '매장' in intent_name:
            time.sleep(5)
            speak("감사합니다. 대기번호를 확인해주세요.")
            return True
        return False

    def close_db_connection(self):
        self.cur.close()
        self.conn.close()
