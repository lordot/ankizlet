from scrapy import signals
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from pydispatch import dispatcher

from quizlet.spiders.cards import CardsSpider

if __name__ == "__main__":
    def crawler_results(signal, sender, item, response, spider):
        print("!!!!!!")

    s = get_project_settings()

    dispatcher.connect(crawler_results, signal=signals.item_scraped)
    configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})
    runner = CrawlerRunner(get_project_settings())

    d = runner.crawl(CardsSpider, urls="https://quizlet.com/274690438/gerund-infinitive-flash-cards/?funnelUUID=d2454f9a-2918-4612-97bf-b991d665cb27")
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
