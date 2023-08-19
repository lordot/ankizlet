import random
import re
import shutil
import urllib.request as urllib2
from os import makedirs
from os.path import dirname, join, realpath

import genanki
from genanki import Model


class DecksPipeline:

    def __init__(self):
        self.media_files = []
        self.decks = []
        self.media_dir = join(dirname(dirname(realpath(__file__))), ".media")
        self.results_dir = join(dirname(dirname(realpath(__file__))), "results")
        self.speed = 100
        self.audio_prefix = "https://quizlet.com"
        self.resizer = "https://quizlet.com/cdn-cgi/image/f=auto,fit=cover,h=200,onerror=redirect,w=220/"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/113.0.0.0 Safari/537.36"
        }

        self.model = Model(
            self._get_random_id(),
            "Basic Quizlet Extended",
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
                    "afmt": "{{FrontText}}\n<hr id=answer>\n{{BackText}}"
                            "\n<br><br>\n{{Image}}\n<br><br>\n{{BackAudio}}"
                },
            ],
            css=".card {font-family: arial; font-size: 20px; "
                "text-align: center; color: black; background-color: white;}"
        )

    def open_spider(self, spider):
        makedirs(self.media_dir, exist_ok=True)
        makedirs(self.results_dir, exist_ok=True)
        self.per_file = spider.settings.get("PER_FILE")

    def process_item(self, item, spider):
        title = item.title
        if not self.per_file:
            title = "Ankizlet::" + title

        deck = genanki.Deck(self._get_random_id(), title)

        for card in item.cards:
            if card.image != '':
                img_name = self._file_download(self.resizer + card.image, spider)
                if img_name:
                    card.image = f"<div><img src='{img_name}'></div>"
                    self.media_files.append(f".media/{img_name}")

            for audio_type in ("f_audio", "b_audio"):
                if getattr(card, audio_type) != "":
                    audio_name = self._file_download(
                        self.audio_prefix + getattr(card, audio_type), spider, ".mp3"
                    )
                    if audio_name:
                        setattr(card, audio_type, "[sound:" + audio_name + "]")
                        self.media_files.append(f".media/{audio_name}")

            note_fields = [
                self._html_format(card.front), card.f_audio, self._html_format(card.back), card.b_audio, card.image
            ]
            note = genanki.Note(model=self.model, fields=note_fields)
            deck.add_note(note)

        self.decks.append(deck)

        if self.per_file:
            title = re.sub(r'[\\/:"*?<>|]+', "", title)
            package = genanki.Package(self.decks)
            package.media_files = self.media_files
            package.write_to_file(join(self.results_dir, title + ".apkg"))
            self.decks.clear()
            self.media_files.clear()

        spider.logger.info(f"Saved: {deck.name}")
        return item

    def close_spider(self, spider):
        if not self.per_file:
            package = genanki.Package(self.decks)
            package.media_files = self.media_files
            package.write_to_file(join(self.results_dir, "output.apkg"))
        shutil.rmtree(self.media_dir)

    def _get_random_id(self):
        return random.randrange(1 << 30, 1 << 31)

    def _file_download(self, url, spider, suffix=""):
        url = url.replace("speed=70", f"speed={self.speed}")
        file_name = "quizlet-" + url.replace("&speed=", "").replace("=", "/").split("/")[-1] + suffix
        try:
            response = urllib2.urlopen(urllib2.Request(url, headers=self.headers))
            if response.getcode() == 200:
                with open(join(self.media_dir, file_name), 'wb') as f:
                    f.write(response.read())
            return file_name
        except urllib2.HTTPError:
            spider.logger.warning(f"Bad URL for media item: {url}")
            return None

    def _html_format(self, string: str):
        return string.replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
