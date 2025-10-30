"""
Script to import style tweets from URLs using tweety-ns.
Reads tweet URLs from scripts/tweets.txt (one URL per line).

Usage:
    1. Add tweet URLs to scripts/tweets.txt (one per line)
    2. Run: python scripts/import_tweets.py
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
# FETCHING LOGIC
# ============================================================================

def load_tweet_urls(file_path: str) -> list[str]:
    """
    Load tweet URLs from a text file (one URL per line).

    Args:
        file_path: Path to the text file containing URLs

    Returns:
        List of tweet URLs
    """
    urls = []

    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        print(f"Creating empty {file_path} file...")
        with open(file_path, 'w') as f:
            f.write("# Add tweet URLs here, one per line\n")
            f.write("# Example: https://twitter.com/sama/status/1234567890\n")
        return urls

    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Basic validation - check if it looks like a Twitter URL
            if 'twitter.com' in line or 'x.com' in line:
                urls.append(line)
            else:
                print(f"⚠️  Line {line_num}: Skipping invalid URL: {line}")

    return urls

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
            tweet = await client.tweet_detail(tweet_id)

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

    # Load tweet URLs from file
    tweets_file = os.path.join(os.path.dirname(__file__), 'tweets.txt')
    print(f"📄 Loading tweet URLs from: {tweets_file}")

    tweet_urls = load_tweet_urls(tweets_file)

    if not tweet_urls:
        print()
        print("⚠️  No tweet URLs found!")
        print()
        print(f"Please add tweet URLs to {tweets_file}")
        print("Format: One URL per line")
        print()
        print("Example:")
        print('  https://twitter.com/sama/status/1234567890123456789')
        print('  https://twitter.com/karpathy/status/9876543210987654321')
        print('  https://x.com/levelsio/status/1234567890123456789')
        print()
        print("Lines starting with # are ignored (comments)")
        return

    print(f"📋 Found {len(tweet_urls)} tweet URLs to import")
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

    for i, url in enumerate(tweet_urls, 1):
        print(f"[{i}/{len(tweet_urls)}] Processing: {url}")

        # Fetch tweet
        tweet_data = await fetch_tweet(client, url)

        if tweet_data:
            # Add to RAG (no categories - keep it simple)
            try:
                rag.add_style_tweet(
                    tweet=tweet_data['text'],
                    author=tweet_data['author'],
                    engagement=tweet_data['engagement'],
                    category=None,
                    url=tweet_data.get('url')
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
        if i < len(tweet_urls):
            await asyncio.sleep(2)

    # Summary
    print("=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Successfully imported: {successful}")
    print(f"❌ Failed: {failed}")
    print()
    print(f"📊 Total tweets in database: {rag.count()}")
    print()
    print("Done! Your RAG database has been updated.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
