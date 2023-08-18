import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QTimer
from subprocess import Popen, PIPE
import threading


class ScrapyGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        screen_size = QApplication.primaryScreen().availableSize()
        self.resize(screen_size.width() // 3, screen_size.height() // 3)

        self.setWindowTitle('Scrapy GUI')

        self.url_textedit = QTextEdit(self)
        self.url_textedit.setPlaceholderText("Enter URLs and passwords (if any) separated by space, next URLs on new lines...")

        self.deck_checkbox = QCheckBox("Deck per file", self)

        self.log_textedit = QTextEdit(self)
        self.log_textedit.setReadOnly(True)

        self.start_button = QPushButton('Start', self)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_scrapy)

        layout = QVBoxLayout()
        layout.addWidget(self.url_textedit)
        layout.addWidget(self.deck_checkbox)
        layout.addWidget(self.log_textedit)
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.url_textedit.textChanged.connect(self.enable_start_button)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_log)
        self.refresh_timer.start(3000)  # Обновление каждые 3000 миллисекунд (3 секунды)

    def enable_start_button(self):
        text = self.url_textedit.toPlainText()
        self.start_button.setEnabled(len(text.strip()) > 0)

    def start_scrapy(self):
        self.start_button.setEnabled(False)
        self.log_textedit.clear()

        urls = self.url_textedit.toPlainText().split('\n')
        urls = [url.strip() for url in urls if url.strip()]

        deck_per_file = self.deck_checkbox.isChecked()

        args = ['scrapy', 'crawl', 'cards', '-a', f'urls={";".join(urls)}']
        if deck_per_file:
            args.extend(['-s', 'PER_FILE=True'])

        def run_scrapy():
            process = Popen(args, stdout=PIPE, stderr=PIPE, text=True)
            for line in process.stdout:
                self.log_textedit.append(line.strip())
            process.communicate()

            if process.returncode == 0:
                result = "Finished"
            else:
                result = f"Error: {process.stderr.read()}"

            self.log_textedit.append(result)
        self.start_button.setEnabled(True)

        threading.Thread(target=run_scrapy).start()

    def refresh_log(self):
        try:
            with open('scrapy.log', 'r') as log_file:
                log_content = log_file.read()
                self.log_textedit.setPlainText(log_content)
        except FileNotFoundError:
            self.log_textedit.setPlainText("No log file found.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrapyGUI()
    window.show()
    sys.exit(app.exec_())
