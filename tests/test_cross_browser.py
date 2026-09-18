import pytest

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

USER, PASS = "standard_user", "secret_sauce"


@pytest.fixture
def inventory(driver):
    LoginPage(driver).open().login(USER, PASS)
    return InventoryPage(driver)


def test_login_success(driver):
    LoginPage(driver).open().login(USER, PASS)
    assert "/inventory.html" in driver.current_url
    assert len(InventoryPage(driver).item_names()) == 6


def test_login_locked_out_shows_error(driver):
    page = LoginPage(driver).open()
    page.login("locked_out_user", PASS)
    assert "locked out" in page.error_message()


def test_navigate_to_item_and_back(driver, inventory):
    name = inventory.item_names()[0]
    assert inventory.open_item(name) == name
    inventory.back_to_products()
    assert "/inventory.html" in driver.current_url


def test_sort_form_reorders_items(driver, inventory):
    inventory.sort_by("za")
    names = inventory.item_names()
    assert names == sorted(names, reverse=True)


def test_checkout_form_flow(driver, inventory):
    inventory.add_to_cart("Sauce Labs Backpack")
    assert inventory.cart_count() == 1
    inventory.go_to_cart()
    cart = CartPage(driver)
    assert cart.item_names() == ["Sauce Labs Backpack"]
    cart.checkout()
    checkout = CheckoutPage(driver)
    checkout.fill_info("Ada", "Lovelace", "12345")
    checkout.finish()
    assert checkout.complete_message() == "Thank you for your order!"
