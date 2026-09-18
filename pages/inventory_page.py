from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class InventoryPage(BasePage):
    ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    SORT_SELECT = (By.CLASS_NAME, "product_sort_container")
    CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")
    CART_LINK = (By.CLASS_NAME, "shopping_cart_link")
    MENU_BUTTON = (By.ID, "react-burger-menu-btn")
    LOGOUT_LINK = (By.ID, "logout_sidebar_link")
    DETAIL_NAME = (By.CLASS_NAME, "inventory_details_name")
    BACK_TO_PRODUCTS = (By.ID, "back-to-products")

    @staticmethod
    def _slug(name):
        return name.lower().replace(" ", "-")

    def item_names(self):
        return [e.text for e in self.find_all(self.ITEM_NAMES)]

    def add_to_cart(self, name):
        self.click((By.ID, f"add-to-cart-{self._slug(name)}"))

    def cart_count(self):
        badges = self.driver.find_elements(*self.CART_BADGE)
        return int(badges[0].text) if badges else 0

    def sort_by(self, value):
        """value: az | za | lohi | hilo"""
        Select(self.find(self.SORT_SELECT)).select_by_value(value)

    def open_item(self, name):
        # Firefox: the <a href="#"> wrapping the name has a zero-size box (inline anchor,
        # block child) so geckodriver throws ElementNotInteractable; click the inner div.
        self.click((By.XPATH, f"//div[contains(@class,'inventory_item_name') and text()='{name}']"))
        return self.text_of(self.DETAIL_NAME)

    def back_to_products(self):
        self.click(self.BACK_TO_PRODUCTS)
        self.wait.until(EC.url_contains("/inventory.html"))

    def go_to_cart(self):
        self.click(self.CART_LINK)
        self.wait.until(EC.url_contains("/cart.html"))

    def logout(self):
        # the burger click can be swallowed while React is still hydrating; re-click
        for _ in range(3):
            self.click(self.MENU_BUTTON)
            try:
                WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located(self.LOGOUT_LINK))
                break
            except TimeoutException:
                pass
        self.click(self.LOGOUT_LINK)
        self.wait.until(EC.url_to_be("https://www.saucedemo.com/"))
