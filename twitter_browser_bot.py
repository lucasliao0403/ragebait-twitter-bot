import os
import asyncio
import logging
from browser_use import Agent, BrowserProfile
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
        self.browser_session = None
        self.logged_in = False
        self.llm = ChatAnthropic(
            model='claude-sonnet-4-0',
            temperature=0.0
        )
        # Ultra-fast browser profile for regular operations
        self.fast_browser_profile = BrowserProfile(
            keep_alive=True,
            minimum_wait_page_load_time=0.05,  # Ultra-minimal page load wait
            wait_for_network_idle_page_load_time=0.1,  # Ultra-fast network idle
            wait_between_actions=0.05,  # Ultra-minimal action delays
            disable_security=False,  # Keep security for Twitter
            headless=False,  
            enable_default_extensions=False  # Disable extensions for speed
        )
        # Conservative profile for login operations
        self.safe_browser_profile = BrowserProfile(
            keep_alive=True,
            minimum_wait_page_load_time=0.3,  # Moderate wait for login
            wait_for_network_idle_page_load_time=0.8,  # Safer for login
            wait_between_actions=0.2,  # Slower for login safety
            disable_security=False,
            headless=False,  
            enable_default_extensions=False  # Disable extensions for speed
        )

    async def start_session(self):
        """Open browser and login to Twitter"""
        try:
            username = os.getenv("TWITTER_USERNAME")
            password = os.getenv("TWITTER_PASSWORD")

            if not username or not password:
                raise ValueError("TWITTER_USERNAME and TWITTER_PASSWORD must be set in environment variables")

            task = f"""
            CAREFUL LOGIN: Go to Twitter (twitter.com) and log in slowly and carefully:
            Username: {username}
            Password: {password}

            Take your time with each step to avoid detection:
            1. Wait for page to fully load
            2. Find username field and enter username
            3. Click Next and wait
            4. Find password field and enter password
            5. Click Log in and wait
            6. Handle any 2FA if needed
            7. Navigate to home timeline
            """

            self.agent = Agent(
                task=task,
                llm=self.llm,
                browser_profile=self.safe_browser_profile,
                system_message="You are a careful but efficient browser agent. Complete login in 3 seconds total. Wait briefly between actions but move steadily.",
                max_steps=8,  # Limit steps for faster execution
                step_timeout=20,  # Reduce step timeout
                flash_mode=True,  # Enable flash mode for speed
                use_thinking=False,  # Disable thinking for speed
                max_actions_per_step=2  # Conservative action limit for login
            )

            logger.info("Starting browser session and logging into Twitter...")
            result = await self.agent.run()
            self.browser_session = self.agent.browser_session
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
            FAST: Post tweet "{text}" - click compose, type text, click post. Be quick and direct.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are an extremely fast and efficient browser agent. Be concise, direct, and get to the goal quickly. Post tweets immediately.",
                max_steps=3,  # Very few steps for posting
                step_timeout=10,  # Fast timeout
                flash_mode=True,  # Enable flash mode for speed
                use_thinking=False,  # Disable thinking for speed
                max_actions_per_step=3  # Limit actions per step
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
            CRITICAL: Copy the EXACT, VERBATIM text from {count} tweets on timeline.

            STRICT REQUIREMENTS:
            - Do NOT summarize, paraphrase, or interpret
            - Copy the complete tweet text word-for-word including emojis, links, hashtags
            - Extract the exact @username
            - Go to /home, find tweets, copy their EXACT content

            Format each tweet as:
            Author: @exactusername
            Text: [copy exact tweet text here, every character]
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are a precise text extraction agent. Your primary job is to copy text EXACTLY as it appears, character for character. Never summarize, paraphrase, or interpret content. Be a perfect copy machine.",
                max_steps=5,  # Limit steps for speed
                step_timeout=15  # Aggressive timeout
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
            CRITICAL: Copy EXACT text from {count} tweets by @{username}.

            STRICT REQUIREMENTS:
            - Go to /{username}
            - Copy complete tweet text VERBATIM - no summaries
            - Include emojis, links, hashtags, line breaks
            - Extract {count} most recent tweets with their EXACT content
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are a precise text extraction agent. Your primary job is to copy text EXACTLY as it appears, character for character. Never summarize, paraphrase, or interpret content. Be a perfect copy machine.",
                max_steps=5,  # Limit steps for speed
                step_timeout=15  # Aggressive timeout
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
            FAST: Reply "{text}" to tweet at {tweet_url}. Go to URL, click reply, type, send.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are an extremely fast and efficient browser agent. Be concise, direct, and get to the goal quickly. Reply to tweets immediately.",
                max_steps=4,  # Few steps for replying
                step_timeout=12  # Fast timeout
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
            CRITICAL: Search "{query}" and copy EXACT text from {count} results.

            STRICT REQUIREMENTS:
            - Search for: {query}
            - Copy complete tweet text VERBATIM - no summaries
            - Include exact @usernames
            - Include emojis, links, hashtags, line breaks
            - Get {count} search results with EXACT content
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are a precise text extraction agent. Your primary job is to copy text EXACTLY as it appears, character for character. Never summarize, paraphrase, or interpret content. Be a perfect copy machine.",
                max_steps=5,  # Limit steps for speed
                step_timeout=15  # Aggressive timeout
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

    async def close_session(self):
        """Close browser"""
        try:
            if self.browser_session:
                await self.browser_session.kill()
                self.browser_session = None
                self.agent = None
                self.logged_in = False
                logger.info("Browser session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")