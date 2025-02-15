import sys
import os
import requests
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
# parecord --device=bluez_output.08_12_87_82_80_4A.a2dp-sink.monitor vlc_audio.wav
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_command(query):
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": f"This is a Ubuntu 22.04 system. Give me the appropriate terminal command to do the following: {query}. Give the command only and nothing else"}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', "Error: No command generated.")
    else:
        return f"Error: {response.status_code}, {response.text}"

class SystemTweakerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("System Tweaker")
        self.setGeometry(200, 200, 500, 150)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Enter your system tweak request:")
        layout.addWidget(self.label)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("E.g., Enable dark mode")
        self.query_input.returnPressed.connect(self.run_command)
        layout.addWidget(self.query_input)
        
        self.run_button = QPushButton("Apply Change")
        self.run_button.clicked.connect(self.run_command)
        layout.addWidget(self.run_button)
        
        self.setLayout(layout)
    
    def run_command(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Input Error", "Please enter a valid query.")
            return
        
        command = get_command(query)
        print(command)
        
        if command.startswith("Error"):
            QMessageBox.critical(self, "API Error", command)
            return
        
        try:
            subprocess.run(command, shell=True, check=True)
            QMessageBox.information(self, "Success", "Command executed successfully!")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Execution Error", "Failed to execute the command.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemTweakerApp()
    window.show()
    sys.exit(app.exec())