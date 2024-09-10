import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from chatgpt_interface import ChatGPTInterface
from google_speech import AudioStream, SpeechRecognizer
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C++面试助手")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setStyleSheet("QTextEdit { font-size: 14pt; }")
        layout.addWidget(self.conversation_display)

        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)

        self.device_combo = QComboBox()
        layout.addWidget(self.device_combo)

        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.audio_stream = AudioStream()
        self.recognizer = SpeechRecognizer()

        self.audio_stream.audioData.connect(self.recognizer.add_audio)
        self.recognizer.textDetected.connect(self.on_text_detected)
        self.audio_stream.error.connect(self.on_audio_error)

        self.populate_audio_devices()

        try:
            self.chatgpt = ChatGPTInterface()
        except ValueError as e:
            self.status_label.setText(f"错误: {str(e)}")
            self.record_button.setEnabled(False)

        self.is_recording = False
        self.partial_text = ""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(100)  # 每100毫秒更新一次显示

    def populate_audio_devices(self):
        devices = self.audio_stream.list_audio_devices()
        for index, name in devices:
            self.device_combo.addItem(f"{name} (Index: {index})", index)

    def toggle_recording(self):
        if not self.is_recording:
            selected_device = self.device_combo.currentData()
            if selected_device is None:
                QMessageBox.warning(self, "错误", "请选择一个音频输入设备")
                return
            self.audio_stream.set_device(selected_device)
            self.record_button.setText("停止录音")
            self.status_label.setText("正在录音...")
            self.audio_stream.start()
            self.recognizer.start()
            self.is_recording = True
        else:
            self.record_button.setText("开始录音")
            self.status_label.setText("正在处理...")
            self.audio_stream.stop()
            self.recognizer.stop()
            self.is_recording = False

    def on_text_detected(self, text):
        self.partial_text = text
        threading.Thread(target=self.get_chatgpt_response, args=(text,)).start()

    def get_chatgpt_response(self, text):
        try:
            response = self.chatgpt.get_response(text)
            formatted_response = self.format_response(response)
            self.conversation_display.append(f"<b>面试者:</b><br>{formatted_response}<br>")
        except Exception as e:
            self.conversation_display.append(f"<span style='color: red;'>错误: 无法获取ChatGPT响应 - {str(e)}</span><br>")
        finally:
            self.status_label.setText("准备就绪")

    def update_display(self):
        if self.partial_text:
            self.conversation_display.append(f"<b>面试官:</b> {self.partial_text}<br>")
            self.partial_text = ""

    def format_response(self, response):
        # [保持不变]
        ...

    def on_audio_error(self, error_message):
        QMessageBox.critical(self, "音频错误", error_message)
        self.record_button.setText("开始录音")
        self.status_label.setText("准备就绪")
        self.is_recording = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())