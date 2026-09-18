from selenium.common.exceptions import (ElementClickInterceptedException, ElementNotInteractableException,
                                        StaleElementReferenceException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    RETRY_ON = (StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException)

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.retry_wait = WebDriverWait(driver, timeout, ignored_exceptions=self.RETRY_ON)

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator):
        self.wait.until(EC.presence_of_element_located(locator))
        return self.driver.find_elements(*locator)

    def click(self, locator):
        # React re-renders can stale an element between locate and click; retry until it lands
        def _click(d):
            el = EC.element_to_be_clickable(locator)(d)
            if not el:
                return False
            el.click()
            return True
        self.retry_wait.until(_click)

    def type(self, locator, text):
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def text_of(self, locator):
        return self.find(locator).text
