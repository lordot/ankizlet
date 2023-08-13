from os.path import dirname, realpath
import random

import genanki
from genanki import Model, Package

import urllib.request as urllib2

from quizlet.items import Deck


SPEED = 100
MEDIA_DIR = dirname(dirname(realpath(__file__))) + "\\.media\\"
AUDIO_PREFIX = "https://quizlet.com"
MODEL_ID = random.randrange(1 << 30, 1 << 31)
RESIZER = "https://quizlet.com/cdn-cgi/image/f=auto,fit=cover,h=200,onerror=redirect,w=220/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

MODEL = Model(
    MODEL_ID,
    "Basic Quizlet Extended - test",
    fields=[
        {"name": "FrontText"},
        {"name": "FrontAudio"},
        {"name": "BackText"},
        {"name": "BackAudio"},
        {"name": "Image"},
    ],
    templates=[
        {
            "name": "Normal",
            "qfmt": "{{FrontText}}\n<br><br>\n{{FrontAudio}}",
            "afmt": "{{FrontText}}\n<hr id=answer>\n{{BackText}}\n<br><br>\n{{Image}}\n<br><br>\n{{BackAudio}}"
        },
        # {
        #     "name": "Reverse",
        #     "qfmt": "{{BackText}}\n<br><br>\n{{BackAudio}}",
        #     "afmt": "{{BackText}}\n<hr id=answer>\n{{FrontText}}\n<br><br>\n{{FrontAudio}}\n{{Image}}"
        # }
    ],
    css=".card {font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white;}"
)


class DecksPipeline:

    def open_spider(self, spider):
        self.decks = []
        self.media_files = []  # TODO: сделать проверку и создание папки .media

    def process_item(self, item: Deck, spider):
        deck = genanki.Deck(self._get_deck_id(), "Root::" + item["title"])

        for card in item.cards:
            f_audio, b_audio, image = '', '', ''  # TODO: переделать Item в dataclass
            front = card["front"]
            back = card["back"]
            if card.get("image"):
                img_name = self._file_download(RESIZER + card["image"], spider)
                if img_name is not None:
                    image = f"<div><img src='{img_name}'></div>"
                    self.media_files.append(f".media/{img_name}")

            if card.get("f_audio"):
                f_name = self._file_download(
                    AUDIO_PREFIX + card["f_audio"], spider, ".mp3"
                )
                if f_name is not None:
                    f_audio = "[sound:" + f_name + "]"
                    self.media_files.append(f".media/{f_name}")

            if card.get("b_audio"):
                b_name = self._file_download(
                    AUDIO_PREFIX + card["b_audio"], spider, ".mp3"
                )
                if b_name is not None:
                    b_audio = "[sound:" + b_name + "]"
                    self.media_files.append(f".media/{b_name}")

            card = genanki.Note(
                model=MODEL,
                fields=[front, f_audio, back, b_audio, image]
            )
            deck.add_note(card)

        self.decks.append(deck)
        spider.logger.info(f"Deck's saved: {deck.name}")
        return item

    def close_spider(self, spider):
        package = genanki.Package(self.decks)
        package.media_files = self.media_files
        package.write_to_file('output.apkg')  # TODO: добавить очистку папки .media

    def _get_deck_id(self):
        return random.randrange(1 << 30, 1 << 31)

    def _file_download(self, url, spider, suffix=""):
        url = url.replace("speed=70", f"speed={SPEED}")
        fl_name = "quizlet-" + url.replace("&speed=", "").replace("=", "/").split("/")[-1] + suffix
        try:
            r = urllib2.urlopen(urllib2.Request(url, headers=HEADERS))
            if r.getcode() == 200:
                with open(MEDIA_DIR + fl_name, 'wb') as f:
                    f.write(r.read())
            return fl_name
        except urllib2.HTTPError as e:
            spider.logger.error(f"Bad URL: {url}")