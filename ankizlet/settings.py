BOT_NAME = "ankizlet"

LOG_LEVEL = "INFO"
# LOG_FILE = "scrapy.log"

HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 86400

SPIDER_MODULES = ["ankizlet.spiders"]
NEWSPIDER_MODULE = "ankizlet.spiders"

ROBOTSTXT_OBEY = True

DOWNLOADER_MIDDLEWARES = {
   "scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware": None,
   "ankizlet.middlewares.SeleniumMiddleware": 543,
}

ITEM_PIPELINES = {
   "ankizlet.pipelines.DecksPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
