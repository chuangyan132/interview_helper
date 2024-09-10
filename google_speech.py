import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/chuang/Downloads/ace-scarab-433821-c2-d9c8f6e669db.json"

import pyaudio
import queue
from google.cloud import speech
from PyQt5.QtCore import QThread, pyqtSignal

class AudioStream(QThread):
    audioData = pyqtSignal(bytes)
    error = pyqtSignal(str)

    def __init__(self, rate=16000, chunk=1024, channels=1):
        super().__init__()
        self.rate = rate
        self.chunk = chunk
        self.channels = channels
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.device_index = None

    def list_audio_devices(self):
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        devices = []
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                devices.append((i, device_info.get('name')))
        return devices

    def set_device(self, index):
        self.device_index = index

    def run(self):
        try:
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      input_device_index=self.device_index,
                                      frames_per_buffer=self.chunk)
            self.is_recording = True
            while self.is_recording:
                data = self.stream.read(self.chunk)
                self.audioData.emit(data)
        except OSError as e:
            self.error.emit(f"音频设备错误: {str(e)}")
        except Exception as e:
            self.error.emit(f"未知错误: {str(e)}")

    def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

class SpeechRecognizer(QThread):
    textDetected = pyqtSignal(str)

    def __init__(self, rate=16000):
        super().__init__()
        self.rate = rate
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code="zh-CN")
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config, interim_results=True)
        self.audio_queue = queue.Queue()
        self.is_recognizing = False

    def run(self):
        def generate_requests():
            while self.is_recognizing:
                try:
                    chunk = self.audio_queue.get(block=False)
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                except queue.Empty:
                    pass

        self.is_recognizing = True
        responses = self.client.streaming_recognize(self.streaming_config, generate_requests())

        try:
            for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if result.is_final:
                    self.textDetected.emit(result.alternatives[0].transcript)
        except Exception as e:
            self.textDetected.emit(f"语音识别错误: {str(e)}")

    def add_audio(self, audio):
        self.audio_queue.put(audio)

    def stop(self):
        self.is_recognizing = False