import json

import scrapy
from scrapy.http import HtmlResponse, Response
import pandas as pd

import undetected_chromedriver as uc

from quizlet.items import Deck, Card


class CardsSpider(scrapy.Spider):
    name = "cards"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.driver = uc.Chrome(headless=True, use_subprocess=False)
        self.logger.info("Chrome driver is opened")

    def start_requests(self):
        data = pd.read_excel('file.xlsx')

        for _, row in data.iterrows():
            url = row['Cards']
            password = row['Password']

            yield scrapy.Request(url, self.parse, cb_kwargs=dict(password=password))

    def parse(self, response: Response, **kwargs):
        json_response: dict = json.loads(response.text)
        title = response.flags[0]["title"]
        deck = Deck(title=title)
        deck.cards.clear()
        try:
            items = json_response["responses"][0]["models"]["studiableItem"]
            for item in items:
                f_side = item["cardSides"][0]["media"][0]
                b_side = item["cardSides"][1]["media"][0]
                f_word = f_side["plainText"]
                b_word = b_side["plainText"]
                f_audio = f_side["ttsSlowUrl"]
                b_audio = b_side["ttsSlowUrl"]
                img = None
                if len(src := item["cardSides"][1]["media"]) > 1:
                    img = src[1]["url"]

                card = Card(
                    front=f_word,
                    back=b_word,
                    image=img if img else None,
                    f_audio=f_audio if f_audio else None,
                    b_audio=b_audio if b_audio else None
                )
                deck.cards.append(card)
        except KeyError as ke:
            print(f"Wrong json response: {ke}")

        self.logger.info(f"Deck's grabbed: {title}"
                         f"; total cards: {len(deck.cards)}")
        yield deck

    def close(self, spider, reason):
        self.driver.quit()
        self.logger.info("Chrome driver is closed")
