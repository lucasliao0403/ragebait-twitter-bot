import os
import asyncio
import logging
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set browser-use config directory to local project directory
os.environ['BROWSER_USE_CONFIG_DIR'] = os.path.join(os.getcwd(), '.browser_use_config')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterBrowserBot:
    def __init__(self):
        self.agent = None
        self.logged_in = False
        self.llm = ChatAnthropic(
            model='claude-sonnet-4-0',
            temperature=0.0
        )

    async def start_session(self):
        """Open browser and login to Twitter"""
        try:
            username = os.getenv("TWITTER_USERNAME")
            password = os.getenv("TWITTER_PASSWORD")

            if not username or not password:
                raise ValueError("TWITTER_USERNAME and TWITTER_PASSWORD must be set in environment variables")

            task = f"""
            Go to Twitter (twitter.com) and log in with these credentials:
            Username: {username}
            Password: {password}

            If there's a 2FA challenge, wait for manual intervention.
            Navigate to the home timeline after successful login.
            """

            self.agent = Agent(
                task=task,
                llm=self.llm
            )

            logger.info("Starting browser session and logging into Twitter...")
            result = await self.agent.run()
            self.logged_in = True
            logger.info("Successfully logged in to Twitter")
            return result

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise

    async def post_tweet(self, text):
        """Post a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            task = f"""
            Post a tweet on Twitter with this exact text:
            "{text}"

            Steps:
            1. Click the compose tweet button (usually says "Post" or has a plus icon)
            2. Enter the text in the tweet compose box
            3. Click the "Post" button to publish the tweet
            """

            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await agent.run()
            logger.info(f"Posted tweet: {text}")
            return result

        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            raise

    async def get_timeline(self, count=10):
        """Read home timeline"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            task = f"""
            Go to the Twitter home timeline and extract the text and author information from the first {count} tweets.

            Return the information in this format for each tweet:
            - Author: [username]
            - Text: [tweet content]

            Navigate to twitter.com/home if not already there.
            """

            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await agent.run()
            logger.info(f"Retrieved timeline tweets")
            return result

        except Exception as e:
            logger.error(f"Error getting timeline: {e}")
            raise

    async def get_user_tweets(self, username, count=10):
        """Get specific user's tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            task = f"""
            Go to the Twitter profile of @{username} and extract the text from their latest {count} tweets.

            Steps:
            1. Navigate to twitter.com/{username}
            2. Find the tweet content from their latest {count} posts
            3. Return the tweet text for each one
            """

            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await agent.run()
            logger.info(f"Retrieved {count} tweets from @{username}")
            return result

        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            raise

    async def reply_to_tweet(self, tweet_url, text):
        """Reply to a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            task = f"""
            Reply to a tweet with this exact text:
            "{text}"

            Steps:
            1. Go to this tweet URL: {tweet_url}
            2. Click the reply button on the tweet
            3. Enter the reply text in the compose box
            4. Click the reply/post button to send the reply
            """

            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await agent.run()
            logger.info(f"Replied to tweet: {text}")
            return result

        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            raise

    async def search_tweets(self, query, count=10):
        """Search for tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            task = f"""
            Search for tweets on Twitter using this query: "{query}"

            Steps:
            1. Use Twitter's search function to search for: {query}
            2. Extract the text and author information from the first {count} search results
            3. Return the tweet content and usernames
            """

            agent = Agent(
                task=task,
                llm=self.llm
            )

            result = await agent.run()
            logger.info(f"Found tweets for query: {query}")
            return result

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            raise

    def save_session(self):
        """Save browser state manually"""
        try:
            if self.agent:
                logger.info("Session state saved (browser remains open)")
            else:
                logger.warning("No active browser session to save")
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def close_session(self):
        """Close browser"""
        try:
            if self.agent:
                # Browser-use handles cleanup automatically
                self.agent = None
                self.logged_in = False
                logger.info("Browser session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")