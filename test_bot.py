#!/usr/bin/env python3

import sys
from twitter_browser_bot import TwitterBrowserBot

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

def main():
    bot = TwitterBrowserBot()

    print("Welcome to Twitter Browser Bot Test CLI!")
    print("Make sure you have set up your .env file with Twitter credentials.")

    while True:
        print_menu()
        choice = input("\nEnter your choice (1-9): ").strip()

        try:
            if choice == "1":
                print("Starting session and logging in...")
                bot.start_session()
                print("✓ Successfully logged in!")

            elif choice == "2":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                text = input("Enter tweet text: ").strip()
                if text:
                    bot.post_tweet(text)
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
                tweets = bot.get_timeline(count)

                print(f"\n--- Timeline ({len(tweets)} tweets) ---")
                for i, tweet in enumerate(tweets, 1):
                    print(f"{i}. @{tweet['author']}: {tweet['text'][:100]}...")
                print("--- End Timeline ---")

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
                tweets = bot.get_user_tweets(username, count)

                print(f"\n--- @{username} Tweets ({len(tweets)} tweets) ---")
                for i, tweet in enumerate(tweets, 1):
                    print(f"{i}. {tweet['text'][:100]}...")
                print("--- End User Tweets ---")

            elif choice == "5":
                if not bot.logged_in:
                    print("❌ Not logged in. Please start session first.")
                    continue

                tweet_url = input("Enter tweet URL: ").strip()
                if not tweet_url:
                    print("❌ Tweet URL cannot be empty.")
                    continue

                reply_text = input("Enter reply text: ").strip()
                if not reply_text:
                    print("❌ Reply text cannot be empty.")
                    continue

                bot.reply_to_tweet(tweet_url, reply_text)
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
                tweets = bot.search_tweets(query, count)

                print(f"\n--- Search Results for '{query}' ({len(tweets)} tweets) ---")
                for i, tweet in enumerate(tweets, 1):
                    print(f"{i}. @{tweet['author']}: {tweet['text'][:100]}...")
                print("--- End Search Results ---")

            elif choice == "7":
                bot.save_session()
                print("✓ Session saved!")

            elif choice == "8":
                bot.close_session()
                print("✓ Session closed!")

            elif choice == "9":
                print("Closing session and exiting...")
                bot.close_session()
                print("Goodbye!")
                sys.exit(0)

            else:
                print("❌ Invalid choice. Please enter a number between 1-9.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Closing session...")
            bot.close_session()
            sys.exit(0)

        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or restart the session.")

if __name__ == "__main__":
    main()