import sys

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QCheckBox, QLabel
import subprocess
import threading


class ScrapyGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        screen_size = QApplication.primaryScreen().availableSize()
        self.resize(screen_size.width() // 2, screen_size.height() // 2)

        self.setWindowTitle('Scrapy GUI')

        self.url_textedit = QTextEdit(self)
        self.url_textedit.setPlaceholderText("Enter URLs and passwords (if any) separated by space, next URLs on new lines...")

        self.deck_checkbox = QCheckBox("Deck per file", self)

        self.log_textedit = QTextEdit(self)
        self.log_textedit.setReadOnly(True)

        self.start_button = QPushButton('Start', self)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_scrapy)

        self.deck_saved_count = 0
        self.deck_saved_label = QLabel("Deck saved count: 0", self)

        layout = QVBoxLayout()
        layout.addWidget(self.url_textedit)
        layout.addWidget(self.deck_checkbox)
        layout.addWidget(self.log_textedit)
        layout.addWidget(self.start_button)
        layout.addWidget(self.deck_saved_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.url_textedit.textChanged.connect(self.enable_start_button)

    def enable_start_button(self):
        text = self.url_textedit.toPlainText()
        self.start_button.setEnabled(len(text.strip()) > 0)

    def start_scrapy(self):
        self.start_button.setEnabled(False)
        self.log_textedit.clear()
        self.deck_saved_count = 0  # Reset the count
        self.update_deck_saved_label()

        urls = self.url_textedit.toPlainText().split('\n')
        urls = [url.strip() for url in urls if url.strip()]

        deck_per_file = self.deck_checkbox.isChecked()

        args = ['scrapy', 'crawl', 'cards', '-a', f'urls={";".join(urls)}']
        if deck_per_file:
            args.extend(['-s', 'PER_FILE=True'])

        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

        def capture_output():
            with process.stdout:
                for line in iter(process.stdout.readline, ''):
                    self.log_textedit.moveCursor(
                        QTextCursor.End)
                    self.log_textedit.insertPlainText(line)
                    if "Deck saved" in line:
                        self.deck_saved_count += 1
                        self.update_deck_saved_label()
            process.wait()

            if process.returncode == 0:
                result = "Finished"
            else:
                result = f"Error: An error occurred while running Scrapy."

            self.log_textedit.append(result)
            self.start_button.setEnabled(True)

        threading.Thread(target=capture_output).start()

    def update_deck_saved_label(self):
        self.deck_saved_label.setText(f"Deck saved count: {self.deck_saved_count}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrapyGUI()
    window.show()
    sys.exit(app.exec_())
