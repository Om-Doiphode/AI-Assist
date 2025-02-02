import pystray
import pyperclip
from PIL import Image
import time
import sys
from langchain_ollama import OllamaLLM
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QThread, pyqtSignal

class SummarizerThread(QThread):
    summary_ready = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        llm = OllamaLLM(model="llama3.2:latest")
        summary = llm.invoke(f"Summarize the following text in 200 words without starting with 'Here is a summary': {self.text}")
        self.summary_ready.emit(summary)


class MainWindow(QMainWindow):
    def __init__(self, text):
        super().__init__()

        self.text = text
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

        self.summarizer_thread = SummarizerThread(self.text)
        self.summarizer_thread.summary_ready.connect(self.display_summary)

    def update_summary(self):
        # Show a temporary message while summarizing
        self.text_edit.setText("Summarizing....")
        self.summarizer_thread.start()

    def display_summary(self, summary_text):
        self.text_edit.setText(summary_text)


def get_selected_text():
    time.sleep(0.1)  # Add a brief delay to ensure text is copied to clipboard
    return pyperclip.paste()


def after_click(icon, query):
    if str(query) == "Summarize Content":
        text = get_selected_text()
        app = QApplication(sys.argv)
        window = MainWindow(text=text)
        window.show()
        app.exec()  # Start the PyQt application event loop
    elif str(query) == "Exit":
        icon.stop()


# Set up system tray icon and menu
image = Image.open("ollama.png")
icon = pystray.Icon("LLMApp", image, "LLMApp",
                    menu=pystray.Menu(
                        pystray.MenuItem("Summarize Content", after_click),
                        pystray.MenuItem("Exit", after_click)))

icon.run()
