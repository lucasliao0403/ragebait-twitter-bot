"""
Script to import style tweets from URLs using tweety-ns.
Add tweet URLs to TWEET_URLS list, run script to fetch and add to RAG database.

Usage:
    python scripts/import_tweets.py
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bot.style_rag import StyleBasedRAG
from tweety import TwitterAsync

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
# FETCHING LOGIC
# ============================================================================

def extract_tweet_id_from_url(url: str) -> str:
    """Extract tweet ID from URL"""
    import re
    match = re.search(r'/status/(\d+)', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract tweet ID from URL: {url}")


def extract_author_from_url(url: str) -> str:
    """Extract Twitter handle from URL"""
    import re
    # URL format: https://twitter.com/username/status/...
    # or https://x.com/username/status/...
    match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status/', url)
    if match:
        return match.group(1)
    return "unknown"


async def fetch_tweet(client, url: str, max_retries=3):
    """
    Fetch tweet text and metadata from URL using tweety-ns.

    Returns:
        dict with keys: text, author, engagement (likes + retweets), url
        or None if fetching failed
    """
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt + 1}/{max_retries}: Fetching {url}")

            # Extract tweet ID
            tweet_id = extract_tweet_id_from_url(url)

            # Fetch tweet details
            tweet = await client.get_tweet_detail(tweet_id)

            # Extract data
            tweet_text = tweet.text
            author = tweet.author.username
            engagement = (tweet.likes or 0) + (tweet.retweet_counts or 0)

            print(f"    ✅ Fetched: @{author}: \"{tweet_text[:60]}...\" ({engagement} engagement)")

            return {
                'text': tweet_text,
                'author': author,
                'engagement': engagement,
                'url': url
            }

        except Exception as e:
            print(f"    ❌ Error fetching tweet: {e}")
            if attempt < max_retries - 1:
                print(f"    Retrying in 3 seconds...")
                await asyncio.sleep(3)
                continue
            return None

    return None


async def main():
    """Main import script"""
    print("=" * 70)
    print("TECH TWITTER STYLE TWEET IMPORTER (tweety-ns)")
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

    # Setup tweety-ns client
    print("🐦 Initializing tweety-ns client...")
    try:
        client = TwitterAsync("tweet_importer_session")

        # Try to load existing session
        try:
            await client.connect()
            print("✅ Connected using saved session")
        except Exception:
            print("⚠️  No saved session found")
            print("You may need to authenticate if rate limits are hit.")
            print("Run this script interactively and call client.start() to login.")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return

    print()
    print("=" * 70)
    print("FETCHING TWEETS")
    print("=" * 70)
    print()

    # Fetch and import each tweet
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

        # Fetch tweet
        tweet_data = await fetch_tweet(client, url)

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
            print(f"  ❌ Failed to fetch tweet")
            failed += 1

        print()

        # Be nice to Twitter - add delay between requests
        if i < len(TWEET_URLS):
            await asyncio.sleep(2)

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
    asyncio.run(main())
