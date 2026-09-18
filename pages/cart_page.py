from selenium.webdriver.common.by import By
from .base_page import BasePage


class CartPage(BasePage):
    ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    CHECKOUT_BUTTON = (By.ID, "checkout")

    def item_names(self):
        self.find(self.CHECKOUT_BUTTON)  # cart-only element; URL flips before React renders the list
        return [e.text for e in self.driver.find_elements(*self.ITEM_NAMES)]

    def checkout(self):
        self.click(self.CHECKOUT_BUTTON)
