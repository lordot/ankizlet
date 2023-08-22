import sys

from pydispatch import dispatcher
from PyQt5 import QtCore
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
                             QMainWindow, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget)
from scrapy import Request, signals
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

from ankizlet import signalizers
from ankizlet.spiders.cards import CardsSpider


class ScrapyWorker(QtCore.QObject):
    update_button = QtCore.pyqtSignal(list)
    update_label = QtCore.pyqtSignal(str, bool)
    request_signal = QtCore.pyqtSignal()
    args = QtCore.pyqtSignal(list)
    update_log = QtCore.pyqtSignal(str)
    clear_log = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ScrapyWorker, self).__init__(parent)
        self.args.connect(self.get_args)

    @QtCore.pyqtSlot()
    def doWork(self):
        self.request_signal.emit()

    @QtCore.pyqtSlot(list)
    def get_args(self, args):
        self.run_process(args[0], args[1], args[2])

    def run_process(self, urls, per_file, turn):
        self.update_button.emit(["In progress...", False])
        self.clear_log.emit()
        self.update_label.emit("saved", False)
        self.update_label.emit("wrong", False)
        self.update_label.emit("timeout", False)
        self.update_label.emit("invalid", False)
        self.update_label.emit("card", False)

        def saved(signal, sender, item, response, spider):
            self.update_log.emit(item.title + " "*10 + "...saved")
            self.update_label.emit("saved", True)

        def wrong_pass(request: Request):
            self.update_log.emit(request.url + " "*10 + "...wrong password")
            self.update_label.emit("wrong", True)

        def invalid_url(url: str):
            self.update_log.emit(url + " "*10 + "...invalid URL")
            self.update_label.emit("invalid", True)

        def timeout_url(request: Request):
            self.update_log.emit(request.url + " "*10 + "...timeout")
            self.update_label.emit("timeout", True)

        def card_saved():
            self.update_label.emit("card", True)

        dispatcher.connect(saved, signals.item_scraped)
        dispatcher.connect(wrong_pass, signalizers.wrong_pass)
        dispatcher.connect(invalid_url, signalizers.invalid_url)
        dispatcher.connect(timeout_url, signalizers.timeout_url)
        dispatcher.connect(card_saved, signalizers.card_saved)

        runner = CrawlerRunner(get_project_settings())
        configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

        d = runner.crawl(CardsSpider, urls=urls, per_file=per_file, turn=turn)

        def __succeedHandler(result):
            self.update_button.emit(["Start", True])

        def __errorHandler(failure):
            print(failure)
            self.update_button.emit(["Start", True])

        d.addCallback(__succeedHandler)
        d.addErrback(__errorHandler)

        if not reactor.running:
            reactor.run(installSignalHandlers=False)


class AnkizletGUI(QMainWindow):

    def __init__(self, parent=None):
        super(AnkizletGUI, self).__init__()
        self.thread = None
        self.worker = None
        self.init_ui()

    def start_thread(self):
        if self.thread:
            self.worker.doWork()

        self.thread = QtCore.QThread(self)
        self.thread.start()

        self.worker = ScrapyWorker()
        self.worker.moveToThread(self.thread)

        self.worker.update_button.connect(self.updateButton)
        self.worker.update_label.connect(self.updateLabel)
        self.worker.request_signal.connect(self.sendArgs)
        self.worker.update_log.connect(self.updateLog)
        self.worker.clear_log.connect(self.clearLog)

        self.worker.doWork()

    def init_ui(self):
        screen_size = QApplication.primaryScreen().availableSize()
        self.resize(screen_size.width() // 2, screen_size.height() // 2)

        self.setWindowTitle('Ankizlet')

        self.url_textedit = QTextEdit(self)
        self.url_textedit.setPlaceholderText(
            "Enter URLs and passwords (if any) separated by space\n"
            "Next URLs on new lines...\n\n"
            "Example: https://quizlet.com/.... password"
        )

        self.deck_checkbox = QCheckBox("Deck per file", self)
        self.turn_checkbox = QCheckBox("Turn cards", self)

        self.log_textedit = QTextEdit(self)
        self.log_textedit.setAcceptRichText(True)
        self.log_textedit.setReadOnly(True)

        self.start_button = QPushButton('Start', self)
        self.start_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_thread)

        self.deck_saved_count = 0
        self.deck_saved_label = QLabel("Saved: 0", self)
        self.deck_timeout_count = 0
        self.deck_timeout_label = QLabel("Timeout: 0", self)
        self.deck_wrongpass_count = 0
        self.deck_wrongpass_label = QLabel("Wrong password: 0", self)
        self.deck_incorrect_count = 0
        self.deck_incorrect_label = QLabel("Invalid URL: 0", self)
        self.cards_count = 0
        self.cards_label = QLabel("Cards: 0", self)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.deck_saved_label)
        horizontal_layout.addWidget(self.deck_timeout_label)
        horizontal_layout.addWidget(self.deck_wrongpass_label)
        horizontal_layout.addWidget(self.deck_incorrect_label)
        horizontal_layout.addWidget(self.cards_label)

        layout = QVBoxLayout()
        layout.addWidget(self.url_textedit)
        layout.addWidget(self.deck_checkbox)
        layout.addWidget(self.turn_checkbox)
        layout.addWidget(self.log_textedit)
        layout.addWidget(self.start_button)
        layout.addLayout(horizontal_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.url_textedit.textChanged.connect(self.enable_start_button)

    def enable_start_button(self):
        text = self.url_textedit.toPlainText()
        self.start_button.setEnabled(len(text.strip()) > 0)

    @QtCore.pyqtSlot()
    def sendArgs(self):
        urls = self.url_textedit.toPlainText().split('\n')
        urls = (url.split(" ") for url in urls if url != "")

        deck_per_file = self.deck_checkbox.isChecked()
        turn_cards = self.turn_checkbox.isChecked()
        self.worker.args.emit([urls, deck_per_file, turn_cards])

    @QtCore.pyqtSlot(list)
    def updateButton(self, button_list):
        self.start_button.setText(button_list[0])
        self.start_button.setEnabled(button_list[1])

    @QtCore.pyqtSlot(str, bool)
    def updateLabel(self, label, state):
        if label == "saved":
            self.deck_saved_count += 1 if state else 0
            self.deck_saved_label.setText(
                f"Saved: {self.deck_saved_count}"
            )
        elif label == "timeout":
            self.deck_timeout_count += 1 if state else 0
            self.deck_timeout_label.setText(
                f"Timeout: {self.deck_timeout_count}"
            )
        elif label == "wrong":
            self.deck_wrongpass_count += 1 if state else 0
            self.deck_wrongpass_label.setText(
                f"Wrong password: {self.deck_wrongpass_count}"
            )
        elif label == "invalid":
            self.deck_incorrect_count += 1 if state else 0
            self.deck_incorrect_label.setText(
                f"Invalid URL: {self.deck_incorrect_count}"
            )
        elif label == "card":
            self.cards_count += 1 if state else 0
            self.cards_label.setText(f"Cards: {self.cards_count}")

    @QtCore.pyqtSlot(str)
    def updateLog(self, text: str):
        self.log_textedit.moveCursor(QTextCursor.End)
        self.log_textedit.insertPlainText(text + "\n")

    @QtCore.pyqtSlot()
    def clearLog(self):
        self.log_textedit.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AnkizletGUI()
    window.show()
    sys.exit(app.exec_())
