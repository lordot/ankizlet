from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from scrapy.utils.reactor import install_reactor

from ankizlet.spiders.cards import CardsSpider


install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

runner = CrawlerRunner(get_project_settings())
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})
d = runner.crawl(CardsSpider, urls=[["https://quizlet.com/581521812/english-a1-verbs-flash-cards/"]], per_file=False, turn=False)

if __name__ == "__main__":
    from twisted.internet import reactor

    def __succeedHandler(result):
        reactor.stop()


    def __errorHandler(failure):
        print(failure)
        reactor.stop()


    d.addCallback(lambda _: __succeedHandler)
    d.addErrback(__errorHandler)

    if not reactor.running:
        reactor.run(installSignalHandlers=False)
