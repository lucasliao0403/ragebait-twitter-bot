#!/usr/bin/env python3

import sys
import os
import asyncio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.twitter_tweety_bot import TwitterTweetyBot
from bot.twitter_browser_bot import TwitterBrowserBot

def print_menu():
    """Print the available commands menu"""
    print("\n=== Twitter Tweety Bot Test CLI ===")
    print("1. Start session (login to Twitter)")
    print("2. Post tweet")
    print("3. Get timeline")
    print("4. Get user tweets")
    print("5. Reply to tweet")
    print("6. Search tweets")
    print("7. Close session")
    print("8. Exit")
    print("====================================")

async def main():
    # Initialize BOTH bots
    tweety_bot = TwitterTweetyBot()      # For fast reads
    browser_bot = TwitterBrowserBot()    # For reliable writes

    print("Welcome to Twitter Hybrid Bot Test CLI!")
    print("Using tweety-ns for reads, browser-use for writes")
    print("Make sure you have set up your .env file with Twitter credentials.")

    while True:
        print_menu()
        choice = input("\nEnter your choice (1-8): ").strip()

        try:
            if choice == "1":
                print("Starting sessions for both bots...")
                print("\n[1/2] Starting tweety-ns session...")
                await tweety_bot.start_session()
                print("✓ Tweety-ns logged in!")

                print("\n[2/2] Starting browser-use session...")
                await browser_bot.start_session()
                print("✓ Browser-use logged in!")

                print("\n✓ Both sessions ready!")

            elif choice == "2":
                if not browser_bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                text = input("Enter tweet text: ").strip()
                if text:
                    print("📝 Posting with browser-use...")
                    await browser_bot.post_tweet(text)
                    print("✓ Tweet posted!")
                else:
                    print("❌ Tweet text cannot be empty.")

            elif choice == "3":
                if not tweety_bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"📖 Fetching {count} tweets with tweety-ns...")
                tweets = await tweety_bot.get_timeline(count)
                print("✓ Timeline fetched successfully!")
                print(f"\n📊 Retrieved {len(tweets)} tweets")

            elif choice == "4":
                if not tweety_bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                username = input("Enter username (without @): ").strip()
                if not username:
                    print("❌ Username cannot be empty.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"📖 Fetching {count} tweets from @{username} with tweety-ns...")
                tweets = await tweety_bot.get_user_tweets(username, count)
                print(f"✓ Tweets from @{username} fetched successfully!")
                print(f"\n📊 Retrieved {len(tweets)} tweets")

            elif choice == "5":
                if not browser_bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                tweet_url = input("Enter tweet URL: ").strip()
                if not tweet_url:
                    print("❌ Tweet URL cannot be empty.")
                    continue

                # Ask if user wants AI-generated or manual reply
                print("\nReply options:")
                print("1. AI-generated reply (using Claude)")
                print("2. Manual reply")
                reply_choice = input("Choose option (1-2): ").strip()

                if reply_choice == "1":
                    print("🤖 Generating AI reply with browser-use...")
                    reply_text = await browser_bot.generate_reply(tweet_url)
                    print(f"\nGenerated reply: {reply_text}")

                    # Ask for confirmation
                    confirm = input("\nPost this reply? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("❌ Reply cancelled.")
                        continue

                elif reply_choice == "2":
                    reply_text = input("Enter reply text: ").strip()
                    if not reply_text:
                        print("❌ Reply text cannot be empty.")
                        continue
                else:
                    print("❌ Invalid choice.")
                    continue

                print("💬 Replying with browser-use...")
                await browser_bot.reply_to_tweet(tweet_url, reply_text)
                print("✓ Reply posted!")

            elif choice == "6":
                if not tweety_bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                query = input("Enter search query: ").strip()
                if not query:
                    print("❌ Search query cannot be empty.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"🔍 Searching for '{query}' with tweety-ns...")
                tweets = await tweety_bot.search_tweets(query, count)
                print(f"✓ Search for '{query}' completed successfully!")
                print(f"\n📊 Found {len(tweets)} tweets")

            elif choice == "7":
                print("Closing both sessions...")
                await tweety_bot.close_session()
                await browser_bot.close_session()
                print("✓ Both sessions closed!")

            elif choice == "8":
                print("Closing sessions and exiting...")
                await tweety_bot.close_session()
                await browser_bot.close_session()
                print("Goodbye!")
                sys.exit(0)

            else:
                print("❌ Invalid choice. Please enter a number between 1-8.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Closing sessions...")
            await tweety_bot.close_session()
            await browser_bot.close_session()
            sys.exit(0)

        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or restart the session.")

if __name__ == "__main__":
    asyncio.run(main())