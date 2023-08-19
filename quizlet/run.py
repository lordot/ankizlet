import sys

from scrapy import signals
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from pydispatch import dispatcher
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor

from PyQt5 import QtCore
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
                             QMainWindow, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget)

from quizlet.spiders.cards import CardsSpider


class ScrapyWorker(QtCore.QObject):
    update_button = QtCore.pyqtSignal(list)
    update_label = QtCore.pyqtSignal(list)
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
        self.run_process(args[0], args[1])

    def run_process(self, urls, per_file):
        self.update_button.emit(["In progress...", False])

        def deck_name(signal, sender, item, response, spider):
            print(item.title)  # TODO: это должен быть сингал в GUI

        configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})
        dispatcher.connect(deck_name, signal=signals.item_scraped)  # TODO: нужны сигналы для подсчета колод и карт
        runner = CrawlerRunner(get_project_settings())

        d = runner.crawl(CardsSpider, urls=urls)  # TODO: нужно переделать в пауке PER_FILE в локальную переменную
        d.addBoth(lambda _: reactor.stop())
        reactor.run(installSignalHandlers=False)

        self.update_button.emit(["Start", True])


class ScrapyGUI(QMainWindow):

    def __init__(self, parent=None):
        super(ScrapyGUI, self).__init__()

        thread = QtCore.QThread(self)
        thread.start()

        self.worker = ScrapyWorker()
        self.worker.moveToThread(thread)

        self.worker.update_button.connect(self.updateButton)
        self.worker.update_label.connect(self.updateLabel)
        self.worker.request_signal.connect(self.sendArgs)
        self.worker.update_log.connect(self.updateLog)
        self.worker.clear_log.connect(self.clearLog)

        self.init_ui()

    def init_ui(self):
        screen_size = QApplication.primaryScreen().availableSize()
        self.resize(screen_size.width() // 2, screen_size.height() // 2)

        self.setWindowTitle('Scrapy GUI')

        self.url_textedit = QTextEdit(self)
        self.url_textedit.setPlaceholderText(
            "Enter URLs and passwords (if any) separated by space, "  # TODO: тут должен быть пример
            "next URLs on new lines..."
        )

        self.deck_checkbox = QCheckBox("Deck per file", self)

        self.log_textedit = QTextEdit(self)
        self.log_textedit.setAcceptRichText(True)
        self.log_textedit.setReadOnly(True)

        self.start_button = QPushButton('Start', self)
        self.start_button.setEnabled(False)

        self.start_button.clicked.connect(self.worker.doWork)

        self.deck_saved_count = 0
        self.deck_saved_label = QLabel("Saved: 0", self)
        self.deck_timeout_count = 0
        self.deck_timeout_label = QLabel("Timeout: 0", self)
        self.deck_wrongpass_count = 0
        self.deck_wrongpass_label = QLabel("Wrong password: 0", self)
        self.deck_incorrect_count = 0
        self.deck_incorrect_label = QLabel("Invalid URL: 0", self)

        self.log_states = {  # TODO: это нафиг
            "Saved: ": [self.deck_saved_count, self.deck_saved_label],
            "Timeout: ": [self.deck_timeout_count, self.deck_timeout_label],
            "Wrong password: ": [self.deck_wrongpass_count,
                                 self.deck_wrongpass_label]
        }

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.deck_saved_label)
        horizontal_layout.addWidget(self.deck_timeout_label)
        horizontal_layout.addWidget(self.deck_wrongpass_label)
        horizontal_layout.addWidget(self.deck_incorrect_label)

        layout = QVBoxLayout()
        layout.addWidget(self.url_textedit)
        layout.addWidget(self.deck_checkbox)
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
        self.worker.args.emit([urls, deck_per_file])

    @QtCore.pyqtSlot(list)
    def updateButton(self, button_list):
        self.start_button.setText(button_list[0])
        self.start_button.setEnabled(button_list[1])

    @QtCore.pyqtSlot(list)
    def updateLabel(self, state):  # TODO: все переделать под сигналы с воркера
        if state[1]:
            self.log_states[state[0]][0] += 1
        else:
            self.log_states[state[0]][0] = 0
        self.log_states[state[0]][1].setText(
            f"{state[0]}{self.log_states[state[0]][0]}")

    @QtCore.pyqtSlot(str)
    def updateLog(self, text: str):
        self.log_textedit.moveCursor(QTextCursor.End)
        self.log_textedit.insertPlainText(text)

    @QtCore.pyqtSlot()
    def clearLog(self):
        self.log_textedit.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrapyGUI()
    window.show()
    sys.exit(app.exec_())
