from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QProgressDialog, QScrollArea, QTextBrowser)
from markdown import markdown  
import os
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_community.document_loaders import PDFPlumberLoader
import subprocess

load_dotenv()

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

groq_api_key = os.getenv('GROQ_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

def get_active_file_path():
    try:
        win_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode("utf-8").strip()
        pid = subprocess.check_output(["xdotool", "getwindowpid", win_id]).decode("utf-8").strip()

        files = subprocess.check_output(["lsof", "-p", pid]).decode("utf-8").split("\n")

        pdf_files = [line.split()[-1] for line in files if line and line.split()[-1].endswith(".pdf")]

        return pdf_files[-1] if pdf_files else "No PDF file found."
    
    except subprocess.CalledProcessError:
        return "Error retrieving file path."

class LoadingWindow(QWidget):
    """Temporary window to show loading message."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setGeometry(300, 300, 300, 100)

        layout = QVBoxLayout()
        self.label = QLabel("Detecting the active PDF file...\nPlease wait.", self)
        layout.addWidget(self.label)

        self.setLayout(layout)
            
pdf_file = get_active_file_path()
with open("/home/hawkeye/Desktop/Ai-Assist/script.log", "a") as log_file:
    log_file.write(f"Detected PDF file: {pdf_file}\n")

class DocumentQnAApp(QWidget):
    def __init__(self, loading_window):
        super().__init__()
        self.initUI()
        self.loading_window = loading_window
        self.embeddings = None
        self.vectors = None
        self.vector_embedding()
    
    def initUI(self):
        self.setWindowTitle("Document Q&A")
        self.setGeometry(100, 100, 600, 600)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        
        self.label = QLabel("Enter your question:")
        self.layout.addWidget(self.label)
        
        self.question_input = QLineEdit(self)
        self.layout.addWidget(self.question_input)
        
        self.ask_button = QPushButton("Ask", self)
        self.ask_button.clicked.connect(self.ask_question)
        self.layout.addWidget(self.ask_button)
        
        self.scroll_area.setWidget(self.container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
    
    def vector_embedding(self):
        if not self.vectors:
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            loader = PDFPlumberLoader(pdf_file)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            final_documents = text_splitter.split_documents(docs[:20])
            self.vectors = FAISS.from_documents(final_documents, self.embeddings)
            self.add_output_text("Vector Store DB is Ready", "gray")
            if self.loading_window:  
                self.loading_window.close()
    
    def ask_question(self):
        question = self.question_input.text()
        if question and self.vectors:
            progress_dialog = QProgressDialog("Generating answer...", None, 0, 0, self)
            progress_dialog.setWindowTitle("Please Wait")
            progress_dialog.setModal(True)
            progress_dialog.setMinimumDuration(100)
            progress_dialog.show()
            
            QApplication.processEvents()
            
            llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile")
            prompt = ChatPromptTemplate.from_template(
                """
                Answer the questions based on the provided context only.
                Please provide the most accurate response based on the question
                <context>
                {context}
                <context>
                Questions:{question}
                """
            )
            
            retriever = self.vectors.as_retriever()
            retrieval_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory
            )
            
            response = retrieval_chain.invoke({'question': question})
            
            progress_dialog.close()
            
            self.add_output_text(f"Question: {question}", "blue")
            self.add_output_text(f"Answer: {response['answer']}", "green")
    
    def add_output_text(self, text, color="black"):
        """Render Markdown-formatted text in PyQt6 using QTextBrowser."""
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True) 
        html_text = markdown(text)
        styled_html = f'<div style="color: {color}; font-size: 14px;">{html_text}</div>'
        
        text_browser.setHtml(styled_html)
        self.layout.addWidget(text_browser)
        
        self.question_input.clear()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())
        
if __name__ == "__main__":
    app = QApplication([])
    loading_window = LoadingWindow()
    loading_window.show()
    window = DocumentQnAApp(loading_window)
    window.show()
    app.exec()