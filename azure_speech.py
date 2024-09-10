import os
import azure.cognitiveservices.speech as speechsdk
from PyQt5.QtCore import QThread, pyqtSignal

class SpeechRecognizer(QThread):
    textDetected = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'), region=os.getenv('SPEECH_REGION'))
        self.speech_config.speech_recognition_language = "zh-CN"
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=self.audio_config)
        self.is_recognizing = False

    def run(self):
        while self.is_recognizing:
            try:
                result = self.speech_recognizer.recognize_once_async().get()
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    self.textDetected.emit(result.text)
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

    def start_recognition(self):
        self.is_recognizing = True
        self.start()

    def stop_recognition(self):
        self.is_recognizing = False
