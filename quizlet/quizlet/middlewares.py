import re

import scrapy.http
from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse
from selenium.common import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import WebElement

API_URL = "https://quizlet.com/webapi/3.9/" \
          "studiable-item-documents?filters%5BstudiableContainerId%5D={}" \
          "&filters%5BstudiableContainerType%5D=1&perPage=1000&page=1"


class SeleniumMiddleware:
    timeout = 6

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request: scrapy.Request, spider):
        try:
            spider.driver.get(request.url)
            password = request.cb_kwargs["password"]

            if password != "nan":
                self._enter_password(spider.driver, password)

            element_present = EC.presence_of_element_located(
                (By.TAG_NAME, 'h1'))  # TODO: сделать проверку на пароль
            WebDriverWait(spider.driver, self.timeout).until(element_present)

            h1 = spider.driver.find_element(By.TAG_NAME, "h1").text
            deck_id = re.search(r"/(\d+)/", spider.driver.current_url).group(1)

            spider.driver.get(API_URL.format(deck_id))
            data = spider.driver.find_element(By.TAG_NAME, "pre").text

            spider.logger.info(f"Loaded API URL: {API_URL.format(deck_id)}")

            return HtmlResponse(
                url=request.url,
                body=data,
                flags=[{"title": h1}],
                request=request,
                encoding='utf8'
            )

        except WebDriverException:
            label = spider.driver.find_elements(
                By.CSS_SELECTOR, "label.UIInput"
            )

            if label and label[0].get_attribute('aria-invalid'):
                spider.logger.error(f"Wrong password for page: {request.url}")
            elif label:
                spider.logger.error(
                    f"Need password for page: {request.url}")
            else:
                spider.logger.error(
                    f"Timed out for page to load: {request.url}")
            raise IgnoreRequest()

    def process_response(self, request: scrapy.Request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

    def _enter_password(self, driver, password):
        actions = ActionChains(driver)
        actions.send_keys(password)
        actions.perform()
        actions.send_keys(Keys.ENTER)
        actions.perform()
