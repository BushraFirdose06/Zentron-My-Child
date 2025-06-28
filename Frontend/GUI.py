import os
import random
import sys
import getpass
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
    QSizePolicy
)
from PyQt5.QtGui import (
    QIcon, QMovie, QColor, QFont, QPixmap,
    QPalette, QPainter, QTextCharFormat, QTextCursor
)
from PyQt5.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QPoint, QRect
)
from dotenv import dotenv_values

# ======================
#  BACKEND INTEGRATION
# ======================

# Load environment variables
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "JARVIS")
current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")

# Get system username
try:
    Username = getpass.getuser()
except Exception:
    Username = "Sir"

def SetAssistantStatus(Status):
    """Update assistant status in Status.data"""
    try:
        with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as f:
            f.write(Status)
    except Exception as e:
        print(f"Error writing status: {e}")

def GetAssistantStatus():
    """Get current assistant status"""
    try:
        with open(os.path.join(TempDirPath, 'Status.data'), "r", encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Available"
    except Exception as e:
        print(f"Error reading status: {e}")
        return "Error"

def ShowTextToScreen(Text):
    """Display text in the UI"""
    try:
        with open(os.path.join(TempDirPath, 'Responses.data'), "w", encoding='utf-8') as f:
            f.write(Text)
    except Exception as e:
        print(f"Error showing text: {e}")

def SetMicrophoneStatus(Command):
    """Update microphone state"""
    try:
        with open(os.path.join(TempDirPath, 'Mic.data'), "w", encoding='utf-8') as f:
            f.write(Command)
    except Exception as e:
        print(f"Error setting mic status: {e}")

def GetMicrophoneStatus():
    """Get current microphone state"""
    try:
        with open(os.path.join(TempDirPath, 'Mic.data'), "r", encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "False"
    except Exception as e:
        print(f"Error reading mic status: {e}")
        return "False"

def TempDirectoryPath(Filename):
    """Get path to temp files"""
    return os.path.join(TempDirPath, Filename)

def GraphicsDirectoryPath(Filename):
    """Get path to graphics"""
    return os.path.join(GraphicsDirPath, Filename)

def AnswerModifier(Answer):
    """Format answer text"""
    try:
        lines = Answer.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)
    except Exception as e:
        print(f"Error modifying answer: {e}")
        return Answer

def QueryModifier(Query):
    """Format user query"""
    try:
        new_query = Query.lower().strip()
        query_words = new_query.split()
        question_words = ['how', 'what', 'who', 'where', 'when', 'why',
                         'which', 'whose', 'whom', 'can you', "what's",
                         "where's", "how's"]
        
        if any(word + " " in new_query for word in question_words):
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + "?" 
            else:
                new_query += "?" 
        else:
            if query_words[-1][-1] in ['.', '?', '!']:
                new_query = new_query[:-1] + "." 
            else:
                new_query += "." 
        return new_query.capitalize()
    except Exception as e:
        print(f"Error modifying query: {e}")
        return Query

# ======================
#  MODERN UI COMPONENTS
# ======================

class AnimatedBackground(QLabel):
    """Full-screen animated background with Jarvis GIF"""
    def _init_(self, parent=None):
        super()._init_(parent)
        self.setAlignment(Qt.AlignCenter)
        try:
            self.movie = QMovie(GraphicsDirectoryPath("Jarvis.gif"))
            self.movie.setScaledSize(QSize(1920, 1080))  # Full HD size
            self.setMovie(self.movie)
            self.movie.start()
        except Exception as e:
            print(f"Error loading background: {e}")
            self.setText("JARVIS AI")
            self.setStyleSheet("background: black; color: white; font-size: 48px;")

class ChatBubble(QListWidgetItem):
    """Custom chat message bubbles"""
    def _init_(self, sender, message, is_user=False):
        super()._init_()
        self.sender = sender
        self.message = message
        self.is_user = is_user
        
        self.setText(f"{sender}: {message}")
        if is_user:
            self.setTextAlignment(Qt.AlignRight)
            self.setForeground(QColor(64, 158, 255))  # Blue for user
        else:
            self.setForeground(QColor(64, 255, 158))  # Green for AI
        
        self.setSizeHint(QSize(-1, self.calculate_height()))

    def calculate_height(self):
        """Calculate dynamic height based on message length"""
        lines = max(1, len(self.message) // 40)
        return 30 + (lines * 20)

class MainWindow(QMainWindow):
    """Primary application window"""
    def _init_(self):
        super()._init_()
        self.setup_ui()
        self.setup_connections()
        
        # Initial state
        SetMicrophoneStatus("False")
        SetAssistantStatus("Available")

    def setup_ui(self):
        """Initialize all UI components"""
        self.setWindowTitle(f"{Assistantname} AI Assistant")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Background
        self.background = AnimatedBackground()
        self.layout.addWidget(self.background)
        
        # Overlay container
        self.overlay = QWidget()
        self.overlay.setStyleSheet("background-color: rgba(0, 10, 20, 180);")
        self.overlay_layout = QVBoxLayout(self.overlay)
        self.overlay_layout.setContentsMargins(20, 20, 20, 20)
        
        # Chat display
        self.chat_display = QListWidget()
        self.chat_display.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                font-size: 16px;
                color: white;
            }
            QScrollBar:vertical {
                background: rgba(100, 100, 100, 50);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(200, 200, 200, 100);
                border-radius: 4px;
            }
        """)
        self.chat_display.setWordWrap(True)
        
        # Input area
        self.input_area = QWidget()
        self.input_layout = QHBoxLayout(self.input_area)
        self.input_layout.setContentsMargins(0, 10, 0, 0)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message or use voice command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 30, 50, 200);
                border: 1px solid #00aaff;
                border-radius: 15px;
                padding: 12px;
                color: white;
                font-size: 16px;
            }
        """)
        
        self.mic_button = QPushButton()
        self.mic_button.setIcon(QIcon(GraphicsDirectoryPath("Mic_off.png")))
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 50, 50, 200);
                border-radius: 20px;
                min-width: 50px;
                min-height: 50px;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 220);
            }
        """)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background: #00aaff;
                color: white;
                border-radius: 15px;
                padding: 12px 24px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background: #0088cc;
            }
        """)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: #ff5555;
                color: white;
                border-radius: 15px;
                padding: 12px 24px;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background: #cc4444;
            }
        """)
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.mic_button)
        self.input_layout.addWidget(self.send_button)
        self.input_layout.addWidget(self.stop_button)
        
        # Status bar
        self.status_bar = QLabel("🟢 System Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                color: #00ffaa;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background: rgba(0, 0, 0, 100);
                border-radius: 5px;
            }
        """)
        
        # Assemble layout
        self.overlay_layout.addWidget(self.chat_display)
        self.overlay_layout.addWidget(self.input_area)
        self.overlay_layout.addWidget(self.status_bar)
        
        self.layout.addWidget(self.overlay)
        
        # Window size
        self.showMaximized()
        
        # Welcome message
        self.show_welcome_message()

    def setup_connections(self):
        """Connect signals and slots"""
        self.mic_button.clicked.connect(self.toggle_microphone)
        self.send_button.clicked.connect(self.send_text_message)
        self.stop_button.clicked.connect(self.stop_processing)
        
        # Message update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chat)
        self.update_timer.start(100)  # Check for new messages every 100ms
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)

    def show_welcome_message(self):
        """Display initial welcome messages"""
        greetings = [
            f"Initializing {Assistantname} systems...",
            f"Hello {Username}, I am {Assistantname}",
            "All systems operational",
            "How may I assist you today?"
        ]
        
        for i, msg in enumerate(greetings):
            QTimer.singleShot(i * 1500, lambda m=msg: self.add_message(Assistantname, m))

    def add_message(self, sender, message):
        """Add a new message to the chat"""
        bubble = ChatBubble(sender, message, sender == Username)
        self.chat_display.addItem(bubble)
        self.chat_display.scrollToBottom()

    def update_chat(self):
        """Check for new messages from backend"""
        try:
            with open(TempDirectoryPath('Responses.data'), "r", encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    if content.startswith(f"{Username}:"):
                        self.add_message(Username, content[len(Username)+2:])
                    else:
                        self.add_message(Assistantname, content)
                    # Clear the file after displaying
                    with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as f:
                        f.write("")
        except Exception as e:
            print(f"Error updating chat: {e}")

    def update_status(self):
        """Update status bar from backend"""
        try:
            status = GetAssistantStatus()
            color = "#00ffaa"  # Green
            if "Listening" in status:
                color = "#ffff00"  # Yellow
            elif "Thinking" in status:
                color = "#ffaa00"  # Orange
            elif "Error" in status:
                color = "#ff5555"  # Red
            
            self.status_bar.setText(f" {status}")
            self.status_bar.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    background: rgba(0, 0, 0, 100);
                    border-radius: 5px;
                }}
            """)
        except Exception as e:
            print(f"Error updating status: {e}")

    def toggle_microphone(self):
        """Toggle microphone state"""
        try:
            current = GetMicrophoneStatus()
            new_state = "False" if current == "True" else "True"
            SetMicrophoneStatus(new_state)
            
            # Update button appearance
            icon = "Mic_on.png" if new_state == "True" else "Mic_off.png"
            self.mic_button.setIcon(QIcon(GraphicsDirectoryPath(icon)))
            
            # Visual feedback
            if new_state == "True":
                self.add_message("System", "Microphone activated - listening...")
            else:
                self.add_message("System", "Microphone deactivated")
        except Exception as e:
            print(f"Error toggling microphone: {e}")

    def send_text_message(self):
        """Send text message from input field"""
        try:
            text = self.input_field.text().strip()
            if text:
                self.add_message(Username, text)
                ShowTextToScreen(f"{Username}: {text}")
                self.input_field.clear()
        except Exception as e:
            print(f"Error sending message: {e}")

    def stop_processing(self):
        """Stop current AI processing"""
        try:
            SetAssistantStatus("Available")
            self.status_bar.setText("🟢 Processing stopped")
            self.add_message("System", "Processing stopped by user")
        except Exception as e:
            print(f"Error stopping processing: {e}")

    def mousePressEvent(self, event):
        """Allow window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if hasattr(self, 'drag_position') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

def GraphicalUserInterface():
    """Initialize and run the GUI"""
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(15, 15, 15))
    dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(40, 40, 40))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()