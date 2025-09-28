import os
import time
import logging
from browser_use import Browser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterBrowserBot:
    def __init__(self):
        self.browser = None
        self.page = None
        self.logged_in = False

    def start_session(self):
        """Open browser and login to Twitter"""
        try:
            # Initialize browser
            self.browser = Browser()
            self.page = self.browser.new_page()

            # Navigate to Twitter login
            logger.info("Navigating to Twitter login...")
            self.page.goto("https://twitter.com/i/flow/login")

            # Wait for page to load
            time.sleep(3)

            # Enter username
            username = os.getenv("TWITTER_USERNAME")
            if not username:
                raise ValueError("TWITTER_USERNAME not set in environment variables")

            username_field = self.page.wait_for_selector('input[name="text"]')
            username_field.fill(username)

            # Click next button
            next_button = self.page.get_by_role("button", name="Next")
            next_button.click()

            time.sleep(2)

            # Enter password
            password = os.getenv("TWITTER_PASSWORD")
            if not password:
                raise ValueError("TWITTER_PASSWORD not set in environment variables")

            password_field = self.page.wait_for_selector('input[name="password"]')
            password_field.fill(password)

            # Click login button
            login_button = self.page.get_by_role("button", name="Log in")
            login_button.click()

            # Check for 2FA or other challenges
            time.sleep(5)

            # Check if we're logged in by looking for home timeline
            try:
                self.page.wait_for_selector('[data-testid="primaryColumn"]', timeout=10000)
                self.logged_in = True
                logger.info("Successfully logged in to Twitter")
            except:
                # Might be 2FA or other challenge
                logger.warning("Login may require 2FA or manual intervention. Please complete and press Enter.")
                input("Press Enter after completing login manually...")
                self.logged_in = True

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            if self.browser:
                self.browser.close()
            raise

    def post_tweet(self, text):
        """Post a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Click on tweet compose button
            compose_button = self.page.get_by_test_id("SideNav_NewTweet_Button")
            compose_button.click()

            time.sleep(2)

            # Enter tweet text
            tweet_textbox = self.page.get_by_test_id("tweetTextarea_0")
            tweet_textbox.fill(text)

            time.sleep(1)

            # Click tweet button
            tweet_button = self.page.get_by_test_id("tweetButtonInline")
            tweet_button.click()

            time.sleep(2)

            logger.info(f"Posted tweet: {text}")

        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            raise

    def get_timeline(self, count=10):
        """Read home timeline"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Navigate to home timeline
            self.page.goto("https://twitter.com/home")
            time.sleep(3)

            tweets = []
            tweet_elements = self.page.get_by_test_id("tweet").take(count)

            for element in tweet_elements:
                try:
                    tweet_text = element.get_by_test_id("tweetText").inner_text()
                    author = element.get_by_test_id("User-Name").inner_text()
                    tweets.append({"author": author, "text": tweet_text})
                except:
                    continue

            logger.info(f"Retrieved {len(tweets)} tweets from timeline")
            return tweets

        except Exception as e:
            logger.error(f"Error getting timeline: {e}")
            raise

    def get_user_tweets(self, username, count=10):
        """Get specific user's tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Navigate to user profile
            self.page.goto(f"https://twitter.com/{username}")
            time.sleep(3)

            tweets = []
            tweet_elements = self.page.get_by_test_id("tweet").take(count)

            for element in tweet_elements:
                try:
                    tweet_text = element.get_by_test_id("tweetText").inner_text()
                    tweets.append({"author": username, "text": tweet_text})
                except:
                    continue

            logger.info(f"Retrieved {len(tweets)} tweets from @{username}")
            return tweets

        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            raise

    def reply_to_tweet(self, tweet_url, text):
        """Reply to a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Navigate to tweet
            self.page.goto(tweet_url)
            time.sleep(3)

            # Click reply button
            reply_button = self.page.get_by_test_id("reply").first
            reply_button.click()

            time.sleep(2)

            # Enter reply text
            reply_textbox = self.page.get_by_test_id("tweetTextarea_0")
            reply_textbox.fill(text)

            time.sleep(1)

            # Click reply button
            send_reply_button = self.page.get_by_test_id("tweetButtonInline")
            send_reply_button.click()

            time.sleep(2)

            logger.info(f"Replied to tweet: {text}")

        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            raise

    def search_tweets(self, query, count=10):
        """Search for tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Navigate to search
            self.page.goto(f"https://twitter.com/search?q={query}&src=typed_query")
            time.sleep(3)

            tweets = []
            tweet_elements = self.page.get_by_test_id("tweet").take(count)

            for element in tweet_elements:
                try:
                    tweet_text = element.get_by_test_id("tweetText").inner_text()
                    author = element.get_by_test_id("User-Name").inner_text()
                    tweets.append({"author": author, "text": tweet_text, "query": query})
                except:
                    continue

            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            raise

    def save_session(self):
        """Save browser state manually"""
        try:
            if self.browser:
                # Save browser context/state
                logger.info("Session state saved (browser remains open)")
            else:
                logger.warning("No active browser session to save")
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def close_session(self):
        """Close browser"""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
                self.page = None
                self.logged_in = False
                logger.info("Browser session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")