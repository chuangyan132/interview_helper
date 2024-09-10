import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSignal, QTimer
from chatgpt_interface import ChatGPTInterface
from azure_speech_detect import SpeechRecognizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azure 语音识别和 ChatGPT 助手")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # 对话展示区
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        layout.addWidget(self.conversation_display)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 无限加载样式
        self.progress_bar.setVisible(False)  # 初始时隐藏
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 初始化语音识别器
        self.recognizer = SpeechRecognizer()
        self.recognizer.textDetected.connect(self.on_text_detected)  # 连接信号槽
        self.recognizer.error.connect(self.on_recognizer_error)

        # 初始化 ChatGPT
        self.chatgpt = ChatGPTInterface()

        # 保存说话者角色
        self.speaker_roles = {}  # 用于存储 speaker_id 和角色 (面试者/面试官)
        self.interviewee_detected = False  # 是否识别到了面试者
        self.interviewer_detected = False  # 是否识别到了面试官

        # 启动录音识别
        self.recognizer.start_recognition()

    def on_text_detected(self, text, speaker_id):
        """处理识别到的文本和说话者ID"""
        if not self.interviewee_detected and speaker_id == "Speaker1":
            # 第一个检测到的声音为面试者
            self.speaker_roles[speaker_id] = "面试者"
            self.interviewee_detected = True
            self.status_label.setText("第一个人在说话")
            self.conversation_display.append("<b>识别到面试者: 闫创</b><br>")

        elif not self.interviewer_detected and speaker_id == "Speaker2":
            # 第二个检测到的声音为面试官
            self.speaker_roles[speaker_id] = "面试官"
            self.interviewer_detected = True
            self.status_label.setText("第二个人在说话")
            self.conversation_display.append("<b>识别到面试官</b><br>")

        # 更新状态为正在听到谁说话
        current_speaker = self.speaker_roles.get(speaker_id, "未知")
        self.status_label.setText(f"{current_speaker}在说话")

        # 如果是面试官提问
        if self.speaker_roles.get(speaker_id) == "面试官":
            self.conversation_display.append(f"<b>面试官:</b> {text}<br>")
            # 显示进度条并启动 ChatGPT 回答
            self.progress_bar.setVisible(True)
            threading.Thread(target=self.process_question, args=(text,)).start()

    def process_question(self, question):
        """处理面试官提问，使用ChatGPT生成回答"""
        response = self.chatgpt.get_response(question)
        self.display_chatgpt_response(response)

    def display_chatgpt_response(self, response):
        """显示ChatGPT生成的回答"""
        formatted_response = self.format_chatgpt_response(response)
        self.conversation_display.append(f"<b>面试者:</b><br>{formatted_response}<br>")
        self.conversation_display.append("<hr>")
        # 隐藏进度条
        self.progress_bar.setVisible(False)

    def format_chatgpt_response(self, response):
        """格式化ChatGPT的回答"""
        formatted_lines = []
        current_indent = ""
        in_answer = False
        answer_content = ""

        for line in response.split('\n'):
            if line.strip().startswith("**答案**"):
                formatted_lines.append(line)
                in_answer = True
            elif line.strip().startswith("**解释**"):
                if in_answer and answer_content:
                    # 将答案内容加上红底白字加粗的格式
                    formatted_lines.append(f'<span style="background-color: red; color: white; font-weight: bold;">{answer_content.strip()}</span>')
                formatted_lines.append(line)
                in_answer = False
                current_indent = "&nbsp;&nbsp;&nbsp;&nbsp;"  # 使用 HTML 空格进行缩进
            elif in_answer:
                answer_content += line + " "
            else:
                # 处理解释部分的列表
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '•', '-', '*')):
                    formatted_lines.append(f"{current_indent}{line}<br>")
                else:
                    formatted_lines.append(f"{current_indent}{line}")

        # 如果回答以答案结束，没有解释部分
        if in_answer and answer_content:
            formatted_lines.append(f'<span style="background-color: red; color: white; font-weight: bold;">{answer_content.strip()}</span>')

        return '<br>'.join(formatted_lines)

    def on_recognizer_error(self, error_message):
        """处理语音识别错误"""
        # 修改错误信息为"无人说话"
        if "未识别到语音" in error_message:
            self.status_label.setText("无人说话")
        else:
            self.status_label.setText(f"错误: {error_message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())