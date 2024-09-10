import os
import azure.cognitiveservices.speech as speechsdk
from PyQt5.QtCore import QThread, pyqtSignal

class SpeechRecognizer(QThread):
    textDetected = pyqtSignal(str, str)  # 信号发送文本和说话者ID
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), region=os.getenv('SPEECH_REGION'))
        self.speech_config.speech_recognition_language = "en-US"
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=self.audio_config)
        self.is_recognizing = False
        self.speaker_count = 0  # 用于模拟生成 speaker_id

    def run(self):
        while self.is_recognizing:
            try:
                result = self.speech_recognizer.recognize_once_async().get()
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    speaker_id = self.get_speaker_id()  # 生成说话者ID
                    self.textDetected.emit(result.text, speaker_id)
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    self.error.emit("未识别到语音")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    error_message = f"语音识别取消: {cancellation_details.reason}"
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        error_message += f" | 错误详情: {cancellation_details.error_details}"
                    self.error.emit(error_message)
            except Exception as e:
                self.error.emit(f"语音识别错误: {str(e)}")

    def get_speaker_id(self):
        """根据顺序生成 speaker_id。第一次返回 Speaker1，第二次返回 Speaker2"""
        if self.speaker_count == 0:
            self.speaker_count += 1
            return "Speaker1"  # 第一个说话者
        else:
            return "Speaker2"  # 第二个说话者

    def start_recognition(self):
        self.is_recognizing = True
        self.start()

    def stop_recognition(self):
        self.is_recognizing = False
