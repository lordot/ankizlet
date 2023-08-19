import json

import scrapy
import undetected_chromedriver as uc
import validators
from scrapy.http import Response

from quizlet.items import Card, Deck


class CardsSpider(scrapy.Spider):
    name = "cards"

    def __init__(self, urls="", **kwargs):
        super().__init__(**kwargs)
        self.driver = uc.Chrome(headless=True, use_subprocess=True)
        self.logger.info("Chrome driver is opened")
        self.urls = tuple(url.split(" ") for url in urls.split(";"))

    def start_requests(self):
        for _, row in enumerate(self.urls):
            password = "nan"
            url = row[0]

            if len(row) > 1:
                password = row[1]

            if validators.url(url):
                yield scrapy.Request(
                    url, self.parse, cb_kwargs=dict(password=password)
                )
            else:
                self.logger.error(f"Invalid URL: {_}")

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

    def _create_card(self, item):  # TODO: добавить возможность отключать аудио с разных сторон
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
