import random
import re
import shutil
import urllib.request as urllib2
from os import makedirs
from os.path import dirname, join, realpath

import genanki

from ankizlet import signalizers


class DecksPipeline:

    def __init__(self):
        self.media_files = []
        self.decks = []
        self.media_dir = join(dirname(dirname(realpath(__file__))), ".media")
        self.results_dir = join(dirname(dirname(realpath(__file__))),
                                "results")
        self.speed = 100
        self.audio_prefix = "https://quizlet.com"
        self.resizer = ("https://quizlet.com/cdn-cgi/image/"
                        "f=auto,fit=cover,h=200,onerror=redirect,w=220/")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/113.0.0.0 Safari/537.36"
        }

    def open_spider(self, spider):
        makedirs(self.media_dir, exist_ok=True)
        makedirs(self.results_dir, exist_ok=True)
        self.model = _get_model(spider.turn)

    def process_item(self, item, spider):
        title = item.title
        if not spider.per_file:
            title = "Ankizlet::" + title

        deck = genanki.Deck(_get_random_id(), title)

        for card in item.cards:
            if card.image != '':
                img_name = self._file_download(self.resizer + card.image,
                                               spider)
                if img_name:
                    card.image = f"<div><img src='{img_name}'></div>"
                    self.media_files.append(f".media/{img_name}")

            for audio_type in ("f_audio", "b_audio"):
                if getattr(card, audio_type) != "":
                    audio_name = self._file_download(
                        getattr(card, audio_type), spider,
                        ".mp3"
                    )
                    if audio_name:
                        setattr(card, audio_type, "[sound:" + audio_name + "]")
                        self.media_files.append(f".media/{audio_name}")

            note_fields = [
                _html_format(card.front), card.f_audio,
                _html_format(card.back), card.b_audio, card.image
            ]
            note = genanki.Note(self.model, fields=note_fields)
            deck.add_note(note)
            spider.crawler.signals.send_catch_log(
                signal=signalizers.card_saved)

        self.decks.append(deck)

        if spider.per_file:
            title = re.sub(r'[\\/:"*?<>|]+', "", title)
            package = genanki.Package(self.decks)
            package.media_files = self.media_files
            package.write_to_file(join(self.results_dir, title + ".apkg"))
            self.decks.clear()
            self.media_files.clear()

        spider.logger.info(f"Saved: {deck.name}")
        return item

    def close_spider(self, spider):
        if not spider.per_file:
            package = genanki.Package(self.decks)
            package.media_files = self.media_files
            package.write_to_file(join(self.results_dir, "output.apkg"))
        shutil.rmtree(self.media_dir)

    def _file_download(self, url, spider, suffix=""):
        url = url.replace("speed=70", f"speed={self.speed}")
        file_name = (
                "quizlet-" + url.replace("&speed=", "").replace("=", "/").
                split("/")[-1] + suffix
        )
        try:
            response = urllib2.urlopen(
                urllib2.Request(url, headers=self.headers))
            if response.getcode() == 200:
                with open(join(self.media_dir, file_name), 'wb') as f:
                    f.write(response.read())
            return file_name
        except urllib2.HTTPError:
            spider.logger.warning(f"Bad URL for media item: {url}")
            return None


def _html_format(string: str):
    return string.replace("<", "&lt;").replace(">", "&gt;").replace("\"",
                                                                    "&quot;")


def _get_random_id():
    return random.randrange(1 << 30, 1 << 31)


def _get_model(turn=False):
    name = "Ankizlet"
    fields = [
        {"name": "FrontText"},
        {"name": "FrontAudio"},
        {"name": "BackText"},
        {"name": "BackAudio"},
        {"name": "Image"},
    ]
    templates = [
        {
            "name": "Normal",
            "qfmt": "{{FrontText}}\n<br><br>\n{{FrontAudio}}",
            "afmt": "{{FrontText}}\n<hr id=answer>\n{{BackText}}"
                    "\n<br><br>\n{{Image}}\n<br><br>\n{{BackAudio}}"
        },
        {
            "name": "Reverse",
            "qfmt": "{{BackText}}\n<br><br>\n{{Image}}\n"
                    "<br><br>\n{{BackAudio}}",
            "afmt": "{{BackText}}\n<hr id=answer>\n{{FrontText}}\n"
                    "<br><br>\n{{FrontAudio}}"
        },
    ]
    css = (".card {font-family: arial; font-size: 20px; "
           "text-align: center; color: black; background-color: white;}")

    if turn:
        name += " Reversed"
        model_id = 1699782351
        templates = templates[1:]
    else:
        model_id = 2119129002
        templates = templates[:1]

    return genanki.Model(model_id, name, fields, templates, css)
