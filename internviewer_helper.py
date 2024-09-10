import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, 
                             QLabel, QProgressBar, QPushButton, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QMetaObject, Q_ARG, Qt
from PyQt5.QtGui import QFont, QKeySequence, QTextCursor
from PyQt5.QtWidgets import QShortcut
from chatgpt_interface import ChatGPTInterface
from azure_speech_detect import SpeechRecognizer

class MainWindow(QMainWindow):
    update_conversation_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azure 语音识别和 ChatGPT 助手")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont('Arial', 8))
        layout.addWidget(self.conversation_display)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        bottom_layout = QHBoxLayout()

        self.status_label = QLabel("准备就绪")
        self.status_label.setFont(QFont('Arial', 8))
        bottom_layout.addWidget(self.status_label)

        # 修改：将重新开始录音按钮改为开始/停止录音按钮
        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self.toggle_recording)
        bottom_layout.addWidget(self.record_button)

        self.chatgpt_toggle_button = QPushButton("启用 ChatGPT")
        self.chatgpt_toggle_button.setCheckable(True)
        self.chatgpt_toggle_button.clicked.connect(self.toggle_chatgpt)
        bottom_layout.addWidget(self.chatgpt_toggle_button)

        layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.recognizer = SpeechRecognizer()
        self.recognizer.textDetected.connect(self.on_text_detected)
        self.recognizer.error.connect(self.on_recognizer_error)

        self.chatgpt = ChatGPTInterface()
        self.chatgpt_enabled = False

        self.speaker_roles = {}
        self.interviewee_detected = False
        self.interviewer_detected = False

        # 修改：初始状态不启动录音
        self.is_recording = False

        self.shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcut.activated.connect(self.toggle_recording)
        self.shortcut.setContext(Qt.ApplicationShortcut)

        self.update_conversation_signal.connect(self.update_conversation_display)

    def toggle_chatgpt(self):
        self.chatgpt_enabled = self.chatgpt_toggle_button.isChecked()
        if self.chatgpt_enabled:
            self.chatgpt_toggle_button.setText("禁用 ChatGPT")
            self.append_to_conversation("<b>ChatGPT 回答已启用</b><br>")
        else:
            self.chatgpt_toggle_button.setText("启用 ChatGPT")
            self.append_to_conversation("<b>ChatGPT 回答已禁用</b><br>")

    # 新增：切换录音状态的方法
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    # 新增：开始录音的方法
    def start_recording(self):
        self.is_recording = True
        self.record_button.setText("结束录音")
        self.conversation_display.clear()
        self.speaker_roles.clear()
        self.interviewee_detected = False
        self.interviewer_detected = False
        self.status_label.setText("正在录音")
        self.recognizer.start_recognition()
        self.append_to_conversation("<b>录音已开始</b><br>")

    # 新增：停止录音的方法
    def stop_recording(self):
        self.is_recording = False
        self.record_button.setText("开始录音")
        self.recognizer.stop_recognition()
        self.status_label.setText("录音已停止")
        self.append_to_conversation("<b>录音已停止</b><br>")
        
        # 自动启动 ChatGPT 服务
        if not self.chatgpt_enabled:
            self.chatgpt_toggle_button.setChecked(True)
            self.toggle_chatgpt()

    def on_text_detected(self, text, speaker_id):
        if not self.interviewee_detected and speaker_id == "Speaker1":
            self.speaker_roles[speaker_id] = "面试者"
            self.interviewee_detected = True
            self.status_label.setText("第一个人在说话")
            self.append_to_conversation("<b>识别到面试者: 闫创</b><br>")
        elif not self.interviewer_detected and speaker_id == "Speaker2":
            self.speaker_roles[speaker_id] = "面试官"
            self.interviewer_detected = True
            self.status_label.setText("第二个人在说话")
            self.append_to_conversation("<b>识别到面试官</b><br>")

        current_speaker = self.speaker_roles.get(speaker_id, "未知")
        self.status_label.setText(f"{current_speaker}在说话")

        if self.speaker_roles.get(speaker_id) == "面试官":
            self.append_to_conversation(f"<b>面试官:</b> {text}<br>")
            if self.chatgpt_enabled:
                self.progress_bar.setVisible(True)
                threading.Thread(target=self.process_question, args=(text,)).start()
            else:
                self.append_to_conversation("<b>ChatGPT 回答已禁用</b><br>")

    def process_question(self, question):
        response = self.chatgpt.get_response(question)
        self.display_chatgpt_response(response)

    def display_chatgpt_response(self, response):
        formatted_response = self.format_chatgpt_response(response)
        self.append_to_conversation(f"<b>面试者:</b><br>{formatted_response}<br><hr>")
        self.progress_bar.setVisible(False)

    def format_chatgpt_response(self, response):
        formatted_lines = []
        
        formatted_lines.append('<div style="font-size: 16px; line-height: 0.7;">')
        
        for line in response.split('\n'):
            if line.strip():
                # Handle bold text
                while '**' in line:
                    line = line.replace('**', '<strong>', 1)
                    line = line.replace('**', '</strong>', 1)
                
                # Handle section titles
                if ':' in line and line.split(':')[0].isupper():
                    parts = line.split(':', 1)
                    line = f'<strong>{parts[0]}:</strong>{parts[1]}'
                
                formatted_lines.append(f"{line}<br>")
    
        formatted_lines.append('</div>')
        return '<br>'.join(formatted_lines)

    def on_recognizer_error(self, error_message):
        if "未识别到语音" in error_message:
            self.status_label.setText("无人说话")
        else:
            self.status_label.setText(f"错误: {error_message}")

    def append_to_conversation(self, text):
        self.update_conversation_signal.emit(text)

    def update_conversation_display(self, text):
        self.conversation_display.append(text)
        self.conversation_display.verticalScrollBar().setValue(
            self.conversation_display.verticalScrollBar().maximum()
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())