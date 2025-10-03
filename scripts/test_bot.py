#!/usr/bin/env python3

import sys
import os
import asyncio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.twitter_browser_bot import TwitterBrowserBot

def print_menu():
    """Print the available commands menu"""
    print("\n=== Twitter Browser Bot Test CLI ===")
    print("1. Start session (login to Twitter)")
    print("2. Post tweet")
    print("3. Get timeline")
    print("4. Get user tweets")
    print("5. Reply to tweet")
    print("6. Search tweets")
    print("7. Save session")
    print("8. Close session")
    print("9. Exit")
    print("=====================================")

async def main():
    bot = TwitterBrowserBot()

    print("Welcome to Twitter Browser Bot Test CLI!")
    print("Make sure you have set up your .env file with Twitter credentials.")

    while True:
        print_menu()
        choice = input("\nEnter your choice (1-9): ").strip()

        try:
            if choice == "1":
                print("Starting session and logging in...")
                await bot.start_session()
                print("✓ Successfully logged in!")

            elif choice == "2":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                text = input("Enter tweet text: ").strip()
                if text:
                    await bot.post_tweet(text)
                    print("✓ Tweet posted!")
                else:
                    print("❌ Tweet text cannot be empty.")

            elif choice == "3":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"Fetching {count} tweets from timeline...")
                result = await bot.get_timeline(count)
                print("✓ Timeline fetched successfully!")


            elif choice == "4":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                username = input("Enter username (without @): ").strip()
                if not username:
                    print("❌ Username cannot be empty.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"Fetching {count} tweets from @{username}...")
                result = await bot.get_user_tweets(username, count)
                print(f"✓ Tweets from @{username} fetched successfully!")


            elif choice == "5":
                if not bot.logged_in:
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
                    print("Generating AI reply...")
                    reply_text = await bot.generate_reply(tweet_url)
                    print(f"\n💡 Generated reply: {reply_text}")

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

                await bot.reply_to_tweet(tweet_url, reply_text)
                print("✓ Reply posted!")

            elif choice == "6":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                query = input("Enter search query: ").strip()
                if not query:
                    print("❌ Search query cannot be empty.")
                    continue

                count = input("Number of tweets to fetch (default 10): ").strip()
                count = int(count) if count.isdigit() else 10

                print(f"Searching for '{query}'...")
                result = await bot.search_tweets(query, count)
                print(f"✓ Search for '{query}' completed successfully!")


            elif choice == "7":
                bot.save_session()
                print("✓ Session saved!")

            elif choice == "8":
                await bot.close_session()
                print("✓ Session closed!")

            elif choice == "9":
                print("Closing session and exiting...")
                await bot.close_session()
                print("Goodbye!")
                sys.exit(0)

            else:
                print("❌ Invalid choice. Please enter a number between 1-9.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Closing session...")
            await bot.close_session()
            sys.exit(0)

        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or restart the session.")

if __name__ == "__main__":
    asyncio.run(main())