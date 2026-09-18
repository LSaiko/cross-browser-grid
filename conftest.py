import base64
import os
from pathlib import Path

import pytest
from pytest_html import extras
from selenium import webdriver

HUB_URL = os.environ.get("HUB_URL", "http://localhost:4444/wd/hub")

OPTIONS = {
    "chrome": webdriver.ChromeOptions,
    "firefox": webdriver.FirefoxOptions,
    "edge": webdriver.EdgeOptions,
}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # on failure: save a screenshot to screenshots/ and embed it in the HTML report
    report = (yield).get_result()
    d = item.funcargs.get("driver")
    if report.when == "call" and report.failed and d:
        png = d.get_screenshot_as_png()
        Path("screenshots").mkdir(exist_ok=True)
        Path(f"screenshots/{item.name}.png").write_bytes(png)
        report.extras = getattr(report, "extras", []) + [extras.png(base64.b64encode(png).decode(), name=item.name)]


# ponytail: starts Chrome-only via BROWSERS env for step-by-step verification; default is all three
@pytest.fixture(params=os.environ.get("BROWSERS", "chrome,firefox,edge").split(","))
def driver(request):
    opts = OPTIONS[request.param]()
    opts.add_argument("--window-size=1280,900")
    d = webdriver.Remote(command_executor=HUB_URL, options=opts)
    d.set_window_size(1280, 900)
    yield d
    d.quit()
