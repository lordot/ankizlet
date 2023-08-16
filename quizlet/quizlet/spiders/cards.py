import json

import numpy as np
import pandas as pd
import scrapy
import undetected_chromedriver as uc
from scrapy.http import Response

from quizlet.items import Card, Deck


class CardsSpider(scrapy.Spider):
    name = "cards"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = uc.Chrome(headless=True, use_subprocess=False)
        self.logger.info("Chrome driver is opened")

    def start_requests(self):
        data = pd.read_excel('file.xlsx')

        for _, row in data.iterrows():
            url = row.get('Cards')
            password = str(row.get('Password'))

            yield scrapy.Request(
                url, self.parse, cb_kwargs=dict(password=password)
            )

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

    def _create_card(self, item):
        f_side = item["cardSides"][0]["media"][0]
        b_side = item["cardSides"][1]["media"][0]
        f_word = f_side["plainText"]
        b_word = b_side["plainText"]
        f_audio = f_side["ttsSlowUrl"]
        b_audio = b_side["ttsSlowUrl"]
        img = item["cardSides"][1]["media"][1]["url"] if len(item["cardSides"][1]["media"]) > 1 else ""

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
