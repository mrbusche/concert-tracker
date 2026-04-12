from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pathlib import Path
import re

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

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
LAZY_LOAD_WAIT_MS = 5000
OUTPUT_DIR = Path('tour')


OUTPUT_DIR.mkdir(exist_ok=True)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(user_agent=USER_AGENT)

    for url in urls:
        try:
            print(f'Fetching {url}...')
            page.goto(url, wait_until='load', timeout=30000)
            # page.wait_for_timeout(LAZY_LOAD_WAIT_MS)

            # Parse the rendered HTML content after the lazy-load wait.
            soup = BeautifulSoup(page.content(), 'html.parser')

            # get_text() grabs text; separator='\n' ensures elements are on new lines
            raw_text = soup.get_text(separator='\n', strip=True)

            # Generate the filename based on your criteria
            # 1. Strip 'http://', 'https://', and 'www.'
            filename = re.sub(r'^https?://(www\.)?', '', url)
            filename = filename.replace('bandsintown.com/a/', '')  # Special case for Bandsintown URLs
            # 2. Strip trailing '/tour', '/on-tour' (for Toad the Wet Sprocket), and standard trailing slashes
            filename = re.sub(r'/tour/?$|/on-tour/?$|/$', '', filename)
            # 3. Replace any remaining slashes with underscores to prevent file path errors
            filename = filename.replace('/', '_') + '.txt'
            output_path = OUTPUT_DIR / filename

            # Save to file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(raw_text)

            print(f'✅ Successfully saved text to {output_path}\n')

        except Exception as e:
            print(f'❌ Failed to fetch {url}. Error: {e}\n')

    browser.close()

print('Scraping complete.')
