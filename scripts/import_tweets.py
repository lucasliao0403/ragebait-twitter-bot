"""
Script to import style tweets from URLs using Selenium scraping.
Add tweet URLs to TWEET_URLS list, run script to scrape and add to RAG database.

Usage:
    python scripts/import_tweets.py
"""

import sys
import os
import time
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Load environment variables from config/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bot.style_rag import StyleBasedRAG

# ============================================================================
# CONFIGURATION: Add your tweet URLs here
# ============================================================================

TWEET_URLS = [
   "https://x.com/mattpocockuk/status/1974528553569137095"
    

    # Add more URLs here...
]

# Optional: Categorize tweets
TWEET_CATEGORIES = {
    # URL -> category mapping
    "https://twitter.com/sama/status/1234567890": "advice",
    "https://twitter.com/karpathy/status/1234567892": "observation",
    # Add more mappings as needed...
}

# ============================================================================
# SCRAPING LOGIC
# ============================================================================

def setup_driver(headless=True):
    """Initialize Chrome WebDriver with options"""
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Disable automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)

    # Execute script to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def extract_author_from_url(url: str) -> str:
    """Extract Twitter handle from URL"""
    # URL format: https://twitter.com/username/status/...
    # or https://x.com/username/status/...
    match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status/', url)
    if match:
        return match.group(1)
    return "unknown"


def scrape_tweet(driver, url: str, max_retries=3):
    """
    Scrape tweet text and metadata from URL.

    Returns:
        dict with keys: text, author, engagement (likes + retweets), url
        or None if scraping failed
    """
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}: Loading {url}")

            driver.get(url)

            # Wait for page to load - look for tweet text
            wait = WebDriverWait(driver, 10)

            # Twitter/X uses article elements for tweets
            # The main tweet is usually the first article with a specific data-testid
            try:
                # Wait for tweet to appear
                tweet_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
                )

                # Give it a moment to fully render
                time.sleep(2)

                # Extract tweet text - it's in a div with specific data-testid or lang attribute
                tweet_text = None

                # Try multiple selectors (Twitter changes these frequently)
                selectors = [
                    'div[data-testid="tweetText"]',
                    'div[lang]',  # Tweet text has lang attribute
                    'div.css-1rynq56',  # Common tweet text class
                ]

                for selector in selectors:
                    try:
                        text_elements = tweet_element.find_elements(By.CSS_SELECTOR, selector)
                        for elem in text_elements:
                            text = elem.text.strip()
                            if text and len(text) > 0:
                                tweet_text = text
                                break
                        if tweet_text:
                            break
                    except:
                        continue

                if not tweet_text:
                    print(f"    ⚠️  Could not extract tweet text")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return None

                # Extract engagement metrics (likes, retweets)
                engagement = 0
                try:
                    # Look for engagement metrics
                    engagement_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="group"] span')
                    for elem in engagement_elements:
                        text = elem.text.strip()
                        # Parse numbers like "1.2K", "500", "2M"
                        if text and any(c.isdigit() for c in text):
                            # Convert to int
                            num_str = text.replace('K', '000').replace('M', '000000').replace(',', '')
                            try:
                                num = int(''.join(c for c in num_str if c.isdigit()))
                                engagement += num
                            except:
                                pass
                except:
                    pass

                # Extract author from URL (more reliable than scraping)
                author = extract_author_from_url(url)

                print(f"    ✅ Scraped: @{author}: \"{tweet_text[:60]}...\" ({engagement} engagement)")

                return {
                    'text': tweet_text,
                    'author': author,
                    'engagement': engagement,
                    'url': url
                }

            except TimeoutException:
                print(f"    ⚠️  Timeout waiting for tweet to load")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return None

        except Exception as e:
            print(f"    ❌ Error scraping tweet: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None

    return None


def main():
    """Main import script"""
    print("=" * 70)
    print("TECH TWITTER STYLE TWEET IMPORTER")
    print("=" * 70)
    print()

    # Check if we have URLs to process
    if not TWEET_URLS or all(url.startswith("https://twitter.com/") and "1234567" in url for url in TWEET_URLS):
        print("⚠️  No real tweet URLs found!")
        print()
        print("Please edit scripts/import_tweets.py and replace the example URLs")
        print("in TWEET_URLS with real Twitter/X URLs you want to import.")
        print()
        print("Example:")
        print('  TWEET_URLS = [')
        print('      "https://twitter.com/sama/status/1234567890123456789",')
        print('      "https://twitter.com/karpathy/status/9876543210987654321",')
        print('  ]')
        return

    print(f"📋 Found {len(TWEET_URLS)} tweet URLs to import")
    print()

    # Initialize RAG database
    rag_db_path = os.path.join(os.getcwd(), '.rag_data')
    print(f"📂 RAG database path: {rag_db_path}")

    rag = StyleBasedRAG(db_path=rag_db_path)
    print(f"📊 Current database size: {rag.count()} style tweets")
    print()

    # Setup Selenium driver
    print("🌐 Starting Chrome WebDriver...")
    try:
        driver = setup_driver(headless=True)
        print("✅ WebDriver ready")
    except Exception as e:
        print(f"❌ Failed to start WebDriver: {e}")
        print()
        print("Make sure you have Chrome and chromedriver installed:")
        print("  brew install chromedriver  # macOS")
        print("  apt-get install chromium-chromedriver  # Linux")
        return

    print()
    print("=" * 70)
    print("SCRAPING TWEETS")
    print("=" * 70)
    print()

    # Scrape and import each tweet
    successful = 0
    failed = 0
    skipped = 0

    for i, url in enumerate(TWEET_URLS, 1):
        print(f"[{i}/{len(TWEET_URLS)}] Processing: {url}")

        # Skip placeholder URLs
        if "1234567" in url:
            print("  ⏭️  Skipping placeholder URL")
            skipped += 1
            continue

        # Scrape tweet
        tweet_data = scrape_tweet(driver, url)

        if tweet_data:
            # Get category if specified
            category = TWEET_CATEGORIES.get(url)

            # Add to RAG
            try:
                rag.add_style_tweet(
                    tweet=tweet_data['text'],
                    author=tweet_data['author'],
                    engagement=tweet_data['engagement'],
                    category=category
                )
                successful += 1
                print(f"  💾 Added to RAG database")
            except Exception as e:
                print(f"  ❌ Failed to add to RAG: {e}")
                failed += 1
        else:
            print(f"  ❌ Failed to scrape tweet")
            failed += 1

        print()

        # Be nice to Twitter - add delay between requests
        if i < len(TWEET_URLS):
            time.sleep(3)

    # Cleanup
    driver.quit()

    # Summary
    print("=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Successfully imported: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped (placeholders): {skipped}")
    print()
    print(f"📊 Total tweets in database: {rag.count()}")
    print()
    print("Done! Your RAG database has been updated.")
    print()


if __name__ == "__main__":
    main()
