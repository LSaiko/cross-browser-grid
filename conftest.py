import os

import pytest
from selenium import webdriver

HUB_URL = os.environ.get("HUB_URL", "http://localhost:4444/wd/hub")

OPTIONS = {
    "chrome": webdriver.ChromeOptions,
    "firefox": webdriver.FirefoxOptions,
    "edge": webdriver.EdgeOptions,
}


# ponytail: starts Chrome-only via BROWSERS env for step-by-step verification; default is both
@pytest.fixture(params=os.environ.get("BROWSERS", "chrome,firefox,edge").split(","))
def driver(request):
    opts = OPTIONS[request.param]()
    opts.add_argument("--window-size=1280,900")
    d = webdriver.Remote(command_executor=HUB_URL, options=opts)
    d.set_window_size(1280, 900)
    yield d
    d.quit()
