import os
from pathlib import Path

import pytest
from selenium import webdriver

HUB_URL = os.environ.get("HUB_URL", "http://localhost:4444/wd/hub")

OPTIONS = {
    "chrome": webdriver.ChromeOptions,
    "firefox": webdriver.FirefoxOptions,
    "edge": webdriver.EdgeOptions,
}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # expose the call-phase report so the fixture can see if the test failed
    outcome = yield
    item.report_call = outcome.get_result() if call.when == "call" else getattr(item, "report_call", None)


# ponytail: starts Chrome-only via BROWSERS env for step-by-step verification; default is all three
@pytest.fixture(params=os.environ.get("BROWSERS", "chrome,firefox,edge").split(","))
def driver(request):
    opts = OPTIONS[request.param]()
    opts.add_argument("--window-size=1280,900")
    d = webdriver.Remote(command_executor=HUB_URL, options=opts)
    d.set_window_size(1280, 900)
    yield d
    report = getattr(request.node, "report_call", None)
    if report and report.failed:
        Path("screenshots").mkdir(exist_ok=True)
        d.save_screenshot(f"screenshots/{request.node.name}.png")
    d.quit()
