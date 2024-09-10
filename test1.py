import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QColor
import pyaudio
import wave
import time
from google.cloud import speech
import io

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/chuang/Downloads/ace-scarab-433821-c2-d9c8f6e669db.json"
class SpeechRecognitionThread(QThread):
    textDetected = pyqtSignal(str)
    statusUpdate = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.client = speech.SpeechClient()

    def run(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        WAVE_OUTPUT_FILENAME = "output.wav"

        while True:
            if self.is_listening:
                self.statusUpdate.emit("准备录音...")
                p = pyaudio.PyAudio()
                try:
                    stream = p.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK)

                    self.statusUpdate.emit("正在录音...")
                    frames = []

                    while self.is_listening:
                        data = stream.read(CHUNK)
                        frames.append(data)

                    self.statusUpdate.emit("录音完成，正在处理...")

                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()

                    # 读取音频文件
                    with io.open(WAVE_OUTPUT_FILENAME, "rb") as audio_file:
                        content = audio_file.read()

                    audio = speech.RecognitionAudio(content=content)
                    config = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=RATE,
                        language_code="zh-CN"  # 设置为中文
                    )

                    # 调用 Google API 进行识别
                    self.statusUpdate.emit("正在识别...")
                    response = self.client.recognize(config=config, audio=audio)

                    for result in response.results:
                        self.textDetected.emit(result.alternatives[0].transcript)
                    
                    self.statusUpdate.emit("识别完成")

                    # 删除临时音频文件
                    os.remove(WAVE_OUTPUT_FILENAME)

                except Exception as e:
                    self.statusUpdate.emit(f"错误: {str(e)}")

            time.sleep(0.1)  # 短暂休眠以减少CPU使用

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音转文字 (Google)")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        self.status_label = QLabel("状态：未监听")
        layout.addWidget(self.status_label)

        self.indicator_label = QLabel("●")
        self.indicator_label.setAlignment(Qt.AlignCenter)
        self.indicator_label.setStyleSheet("font-size: 24pt; color: gray;")
        layout.addWidget(self.indicator_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.speech_thread = SpeechRecognitionThread()
        self.speech_thread.textDetected.connect(self.update_text)
        self.speech_thread.statusUpdate.connect(self.update_status)
        self.speech_thread.start()

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink_indicator)
        self.blink_state = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.toggle_listening()

    def toggle_listening(self):
        self.speech_thread.is_listening = not self.speech_thread.is_listening
        if self.speech_thread.is_listening:
            self.status_label.setText("状态：正在监听")
            self.blink_timer.start(500)  # 每500毫秒闪烁一次
        else:
            self.status_label.setText("状态：停止监听")
            self.blink_timer.stop()
            self.indicator_label.setStyleSheet("font-size: 24pt; color: gray;")
        print(f"{'开始' if self.speech_thread.is_listening else '停止'}监听")

    def update_text(self, text):
        self.text_edit.append(text)

    def update_status(self, status):
        self.status_label.setText(f"状态：{status}")
        print(status)

    def blink_indicator(self):
        self.blink_state = not self.blink_state
        color = "red" if self.blink_state else "gray"
        self.indicator_label.setStyleSheet(f"font-size: 24pt; color: {color};")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())