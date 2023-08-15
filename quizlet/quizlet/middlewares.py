import re
from time import sleep

import scrapy.http
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse
from selenium.common import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from scrapy import signals

API_URL = "https://quizlet.com/webapi/3.9/studiable-item-documents?filters%5BstudiableContainerId%5D={}" \
          "&filters%5BstudiableContainerType%5D=1&perPage=1000&page=1"


class SeleniumMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request: scrapy.Request, spider):
        spider.driver.get(request.url)

        actions = ActionChains(spider.driver)
        actions.send_keys(request.cb_kwargs["password"])
        actions.perform()
        actions.send_keys(Keys.ENTER)
        actions.perform()

        timeout = 6
        try:
            element_present = EC.presence_of_element_located((By.TAG_NAME, 'h1'))
            WebDriverWait(spider.driver, timeout).until(element_present)
            h1 = spider.driver.find_element(By.TAG_NAME, "h1").text
            url_id = re.search(r"/(\d+)/", spider.driver.current_url).group(1)

            spider.driver.get(API_URL.format(url_id))
            data = spider.driver.find_element(By.TAG_NAME, "pre").text

            spider.logger.info(f"Loaded API URL: {API_URL.format(url_id)}")

            return HtmlResponse(
                url=request.url,
                body=data,
                flags=[{"title": h1}],
                request=request,
                encoding='utf8'
            )

        except TimeoutException:
            spider.logger.error(f"Timed out waiting for page to load: {request.url}")
            raise IgnoreRequest()

    def process_response(self, request: scrapy.Request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
