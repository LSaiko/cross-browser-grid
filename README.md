# cross-browser-grid

[![CI](https://github.com/LSaiko/cross-browser-grid/actions/workflows/test.yml/badge.svg)](https://github.com/LSaiko/cross-browser-grid/actions/workflows/test.yml)

Runs one pytest suite against Chrome **and** Firefox through a Selenium Grid
started with Docker Compose. Target app: https://www.saucedemo.com.

## Run it

```bash
docker compose up -d
pip install -r requirements.txt
pytest -v                 # both browsers, 10 tests
BROWSERS=chrome pytest    # one browser
pytest -n 4               # parallel (pytest-xdist) — each node has 2 slots
docker compose down -v
```

Grid console: http://localhost:4444/ui · status JSON: http://localhost:4444/status

## Layout

```
docker-compose.yml     hub + chrome node + firefox node
conftest.py            `driver` fixture, params=["chrome","firefox"], webdriver.Remote → hub
pages/                 POM (login, inventory, cart, checkout) reused from saucedemo-automation
tests/test_cross_browser.py   5 flows: login, bad login, item navigation, sort <select>, checkout form
.github/workflows/test.yml    compose up → wait for hub + 2 nodes → pytest → compose down
```

## Grid architecture

```
 pytest ──HTTP (W3C WebDriver)──▶ selenium-hub :4444
                                    │ event bus :4442/:4443
                     ┌──────────────┴──────────────┐
             node-chrome (2 slots)         node-firefox (2 slots)
             chromedriver + Chrome         geckodriver + Firefox
```

* **Hub** = router + distributor + session map. It receives `POST /session`,
  matches the requested `browserName` against slots the nodes advertised, and
  proxies every subsequent command to the node that owns that session.
* **Nodes** register themselves over the event bus (`SE_EVENT_BUS_HOST`), so
  adding a browser is one more compose service, not a code change.
* `shm_size: 2g` — Chrome/Firefox crash on Docker's default 64 MB `/dev/shm`.

## Why RemoteWebDriver, not local drivers

* One fixture, one code path. `webdriver.Remote(hub, options=...)` only varies
  by the `Options` class; the tests never know where the browser runs.
* The browser + driver versions are pinned by the image tag (`4.27`), not by
  whatever is installed on the dev laptop or CI runner. No Selenium Manager
  downloads, no "works on my machine".
* Scaling is a compose flag (`--scale chrome=3`) and the hub load-balances;
  `pytest -n` then actually runs in parallel (10 tests: 39 s → 17 s here).
* CI runners are headless Linux; the Grid gives them real browser binaries
  without installing anything on the runner.

## Cross-browser differences found

### 1. Firefox refuses to click `<a href="#"><div>…</div></a>` (real failure)

`InventoryPage.open_item` originally clicked `(By.LINK_TEXT, name)`.
Chrome passed, Firefox failed every time:

```
ElementNotInteractableException: Element <a id="item_4_title_link" href="#">
could not be scrolled into view
```

saucedemo wraps a block-level `<div class="inventory_item_name">` in an inline
anchor. geckodriver computes the anchor's own box, which is 0×0, and declines
to click it; chromedriver clicks the anchor's rendered child box instead.
Fix: click the inner `div` (XPath on `inventory_item_name` + text). Both
browsers pass. Lesson: prefer locating the element that actually paints.

### 2. Firefox session start is ~3–5× slower

Per-test `setup` (session create + first `get`), same machine, serial:

| browser | setup (typical) | setup (worst seen) |
|---------|-----------------|--------------------|
| chrome  | 0.3 – 1.4 s     | 1.4 s              |
| firefox | 2.0 – 4.2 s     | 6.7 s              |

Not a failure, but it dominates wall time: firefox contributes ~60% of a
serial run. Session-scoped drivers would hide it but leak state between tests.

### 3. Firefox first-page latency spike (flaky timing, not flaky result)

`test_login_success[firefox]` took 22.4 s on one run vs 2.5 s on the others
(same test, same Grid, nothing else running). Chrome never exceeded 2 s. All
runs still passed because the page objects use explicit 15 s waits per
element rather than sleeps. If this shows up in CI as a timeout, raise
`BasePage` timeout for firefox only — don't add sleeps.

### Not different (checked)

* `<select>` sort via `Select.select_by_value` — identical result order.
* `[data-test='error']` text for locked-out user — identical.
* Checkout form typing/clearing, cart badge count — identical.

## Verification log

* `docker compose up -d` → `/status` reports `ready: true`, 2 nodes
  (`chrome ×2 slots`, `firefox ×2 slots`).
* `BROWSERS=chrome pytest` → 5 passed (13 s).
* `pytest` → 9 passed / 1 failed (finding #1) → fixed → 10 passed, 3 further
  full runs green (28 s, 39 s, 59 s serial; 17 s with `-n 4`).
