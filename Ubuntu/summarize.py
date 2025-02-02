import pyperclip
import time
import sys
from langchain_ollama import OllamaLLM
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QComboBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import requests
import os
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_selected_text():
    time.sleep(0.1)  # Add a brief delay to ensure text is copied to clipboard
    return pyperclip.paste()

class SummarizerThread(QThread):
    summary_ready = pyqtSignal(str)

    def __init__(self, text,type):
        super().__init__()
        self.text = text
        self.type = type

    def run(self):
        if self.type=="Local":
            print("Using Local LLM...")
            llm = OllamaLLM(model="llama3.2:latest")
            summary = llm.invoke(f"Summarize the following text in 200 words without starting with 'Here is a summary': {self.text}")
            self.summary_ready.emit(summary)
            
        elif self.type=="API":
            print("Using Groq API...")
            data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "user", "content": f"Summarize the following text in 200 words without starting with 'Here is a summary': {self.text}"}
                ]
            }

            # Set headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
            
            # Make API request
            response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                summary = response.json().get('choices', [{}])[0].get('message', {}).get('content', "Error: No summary generated.")
            else:
                summary = f"Error: {response.status_code}, {response.text}"
                
            self.summary_ready.emit(summary)

class SummarizerWindow(QMainWindow):
    def __init__(self, text, type):
        super().__init__()

        self.text = text
        self.type = type
        self.setWindowTitle("Summarize Content")
        self.setGeometry(100, 100, 600, 400)

        # Create a text edit widget to show the summary
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)  # Make it read-only so the user can't modify it
        self.text_edit.setText(self.text)

        # Create a button that will trigger the update of the summary
        self.button = QPushButton("Show Summarized Content", self)
        self.button.clicked.connect(self.update_summary)

        # Create a layout to arrange widgets
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.button)

        # Set up a container widget and set it as central widget
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.summarizer_thread = SummarizerThread(self.text,self.type)
        self.summarizer_thread.summary_ready.connect(self.display_summary)

    def update_summary(self):
        # Show a temporary message while summarizing
        self.text_edit.setText("Summarizing....")
        self.summarizer_thread.start()
        self.button.setEnabled(False)

    def display_summary(self, summary_text):
        self.text_edit.setText(summary_text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIAssist")
        self.setGeometry(100, 100, 600, 400)
        self.button = QPushButton("Summarizer")
        self.button.setFixedSize(200, 50)  
        self.button.setStyleSheet("font-size: 16px;")  
        self.button.setCheckable(True)
        self.button.clicked.connect(self.summarize)
        self.comboBox = QComboBox()
        self.comboBox.addItems(['Local','API'])

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add widgets with bottom-right alignment
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.comboBox, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def summarize(self):
        self.type = self.comboBox.currentText()
        text = get_selected_text()
        self.summary_window = SummarizerWindow(text=text, type = self.type)
        self.summary_window.show()

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()