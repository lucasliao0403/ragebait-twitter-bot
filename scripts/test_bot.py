#!/usr/bin/env python3

import sys
import os
import asyncio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.tweety_bot import TweetyBot
from bot.browser_bot import BrowserBot

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
    tweety_bot = TweetyBot()      # For reading tweets
    browser_bot = BrowserBot()    # For posting tweets

    print("Welcome to Ragebait Bot Test CLI!")

    while True:
        print_menu()
        choice = input("\nEnter your choice (1-8): ").strip()

        try:
            # authenticate both bots
            if choice == "1":
                print("Starting sessions for both bots...")
                print("\n[1/2] Starting tweety-ns session...")
                await tweety_bot.start_session()
                print("✓ Tweety-ns logged in!")

                print("\n[2/2] Starting browser-use session...")
                await browser_bot.start_session()
                print("✓ Browser-use logged in!")

                print("\n✓ Both sessions ready!")

            # post tweet
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

            # get timeline
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

            # get user tweets
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

            # reply to tweet
            elif choice == "5":
                # Need both bots: tweety reads tweet, browser posts reply
                if not tweety_bot.logged_in or not browser_bot.logged_in:
                    print("❌ Both bots must be logged in. Please start session first.")
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
                    print("🤖 Generating AI reply with tweety-ns + Claude...")
                    reply_text = await tweety_bot.generate_reply(tweet_url)
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

                print("💬 Posting reply with browser-use...")
                await browser_bot.reply_to_tweet(tweet_url, reply_text)
                print("✓ Reply posted!")

            # search tweets
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

            # close sessions
            elif choice == "7":
                print("Closing both sessions...")
                await tweety_bot.close_session()
                await browser_bot.close_session()
                print("✓ Both sessions closed!")

            # exit
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