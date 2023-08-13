import scrapy


class Card(scrapy.Item):
    front = scrapy.Field()
    back = scrapy.Field()
    image = scrapy.Field()
    f_audio = scrapy.Field()
    b_audio = scrapy.Field()


class Deck(scrapy.Item):
    title: str = scrapy.Field()
    cards: list[Card] = []
