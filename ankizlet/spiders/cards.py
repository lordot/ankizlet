import json
from typing import Generator, Iterator

import scrapy
import undetected_chromedriver as uc
import validators
from scrapy.http import Response

from ankizlet import signalizers
from ankizlet.items import Card, Deck


class CardsSpider(scrapy.Spider):
    name = "cards"

    def __init__(
            self,
            urls: Generator | Iterator = None,
            per_file: bool = False,
            turn: bool = False,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.driver = uc.Chrome(
            headless=True,
            use_subprocess=True,
            driver_executable_path="chromedriver-win64/chromedriver.exe"
        )
        self.logger.info("Chrome driver is opened")
        self.urls = urls
        self.per_file = per_file
        self.turn = turn

    def start_requests(self):
        for row in self.urls:
            password = None
            url = row[0]

            if len(row) > 1:
                password = row[1]

            if validators.url(url):
                yield scrapy.Request(
                    url, self.parse, cb_kwargs=dict(password=password)
                )
            else:
                self.crawler.signals.send_catch_log(
                    signal=signalizers.invalid_url, url=url)
                self.logger.error(f"Invalid URL: {url}")

    def parse(self, response: Response, **kwargs):
        json_response: dict = json.loads(response.text)
        title = response.flags[0]["title"]
        deck = Deck(title)
        deck.cards.clear()

        try:
            items = json_response["responses"][0]["models"]["studiableItem"]
            for item in items:
                card = self._create_card(item)
                deck.cards.append(card)
        except KeyError as ke:
            print(f"Wrong json response: {ke}")

        self.logger.info(f"Deck's grabbed: {title}"
                         f"; total cards: {len(deck.cards)}")
        yield deck

    def _create_card(self, item):  # TODO: добавить возможность отключать аудио
        f_side = item["cardSides"][0]["media"][0]
        b_side = item["cardSides"][1]["media"][0]
        f_word = f_side["plainText"]
        b_word = b_side["plainText"]
        f_audio = f_side["ttsSlowUrl"]
        b_audio = b_side["ttsSlowUrl"]
        img = item["cardSides"][1]["media"][1]["url"] if len(
            item["cardSides"][1]["media"]) > 1 else ""

        return Card(
            front=f_word if f_word else "",
            back=b_word if b_word else "",
            image=img,
            f_audio=f_audio if f_audio else "",
            b_audio=b_audio if b_audio else ""
        )

    def close(self, spider, reason):
        self.driver.quit()
        self.logger.info("Chrome driver is closed")
