import re
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

urls = [
    'https://www.bandsintown.com/a/98-jimmy-eat-world',
    'https://www.bandsintown.com/a/297-third-eye-blind',
    'https://www.bandsintown.com/a/327-the-offspring',
    'https://www.bandsintown.com/a/2815-toad-the-wet-sprocket',
    'https://www.bandsintown.com/a/140-weezer',
    'https://www.bandsintown.com/a/118-rise-against',
    'https://www.bandsintown.com/a/6986370-twenty-one-pilots',
    'https://www.bandsintown.com/a/3240819-the-glorious-sons',
    'https://www.bandsintown.com/a/254-green-day',
    'https://www.bandsintown.com/a/26632-rage-against-the-machine',
    'https://www.bandsintown.com/a/230-shinedown',
    'https://www.bandsintown.com/a/303-chevelle',
    'https://www.bandsintown.com/a/61-goo-goo-dolls',
]

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
LAZY_LOAD_WAIT_MS = 5000
SHOW_MORE_TIMEOUT_MS = 5000
OUTPUT_DIR = Path('tour')
VIEWPORT = {'width': 1440, 'height': 2200}
STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
"""


OUTPUT_DIR.mkdir(exist_ok=True)


def expand_show_more_dates(page):
    event_links = page.locator("a[href*='/e/']")
    initial_event_count = event_links.count()
    show_more_dates = page.locator('div', has_text='Show More Dates').first

    if not show_more_dates.count():
        page.wait_for_timeout(LAZY_LOAD_WAIT_MS)
        return

    try:
        show_more_dates.click(force=True, timeout=SHOW_MORE_TIMEOUT_MS)
        page.wait_for_timeout(LAZY_LOAD_WAIT_MS)

        if event_links.count() == initial_event_count and show_more_dates.count():
            show_more_dates.click(force=True, timeout=SHOW_MORE_TIMEOUT_MS)
            page.wait_for_timeout(LAZY_LOAD_WAIT_MS)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(LAZY_LOAD_WAIT_MS)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled'],
    )
    context = browser.new_context(user_agent=USER_AGENT, viewport=VIEWPORT, locale='en-US')
    context.add_init_script(STEALTH_INIT_SCRIPT)
    page = context.new_page()

    for url in urls:
        try:
            print(f'Fetching {url}...')
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            expand_show_more_dates(page)

            # Parse the rendered HTML content after the lazy-load wait.
            soup = BeautifulSoup(page.content(), 'html.parser')

            # get_text() grabs text; separator='\n' ensures elements are on new lines
            raw_text = soup.get_text(separator='\n', strip=True)

            # Remove any trailing embedded HTML payload that starts at a doctype marker.
            raw_text = re.split(r'<!doctype html>', raw_text, flags=re.IGNORECASE)[0].rstrip()

            # Generate the filename based on your criteria
            # 1. Strip 'http://', 'https://', and 'www.'
            filename = re.sub(r'^https?://(www\.)?', '', url)
            filename = filename.replace('bandsintown.com/a/', '')  # Special case for Bandsintown URLs
            # 2. Strip trailing '/tour', '/on-tour' (for Toad the Wet Sprocket), and standard trailing slashes
            filename = re.sub(r'/tour/?$|/on-tour/?$|/$', '', filename)
            # 3. Remove numeric prefixes and hyphens from the derived filename
            filename = re.sub(r'\d+', '', filename)
            filename = filename.replace('-', '')
            # 4. Replace any remaining slashes with underscores to prevent file path errors
            filename = filename.replace('/', '_') + '.txt'
            output_path = OUTPUT_DIR / filename

            # Save to file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(raw_text)

            print(f'✅ Successfully saved text to {output_path}\n')

        except Exception as e:
            print(f'❌ Failed to fetch {url}. Error: {e}\n')

    context.close()
    browser.close()

print('Scraping complete.')
