import os
import asyncio
import logging
from browser_use import Agent, BrowserProfile
from browser_use.llm import ChatGroq
from dotenv import load_dotenv
from .memory_manager import MemoryManager

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))

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
        self.memory_manager = MemoryManager()

        api_key = os.getenv('GROQ_API_KEY')
        try:
            self.llm = ChatGroq(
                model='meta-llama/llama-4-scout-17b-16e-instruct',
                api_key=api_key,
                temperature=0.0
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq: {e}")
            raise
        # Ultra-fast browser profile for regular operations
        self.fast_browser_profile = BrowserProfile(
            keep_alive=True,
            minimum_wait_page_load_time=0.05,  # Ultra-minimal page load wait
            wait_for_network_idle_page_load_time=0.1,  # Ultra-fast network idle
            wait_between_actions=0.05,  # Ultra-minimal action delays
            disable_security=False,  # Keep security for Twitter
            headless=False,
            enable_default_extensions=False,  # Disable extensions for speed
            user_data_dir=os.path.join(os.getcwd(), '.browser_profile')  # Persistent session storage
        )
        # Conservative profile for login operations
        self.safe_browser_profile = BrowserProfile(
            keep_alive=True,
            minimum_wait_page_load_time=0.3,  # Moderate wait for login
            wait_for_network_idle_page_load_time=0.8,  # Safer for login
            wait_between_actions=0.2,  # Slower for login safety
            disable_security=False,
            headless=False,
            enable_default_extensions=False,  # Disable extensions for speed
            user_data_dir=os.path.join(os.getcwd(), '.browser_profile')  # Persistent session storage
        )

    def _parse_tweets_from_result(self, result_text: str):
        """Parse tweets from agent result and filter ads"""
        tweets = []
        lines = result_text.split('\n')
        current_tweet = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Author: @'):
                if current_tweet:
                    tweets.append(current_tweet)
                current_tweet = {'author': line[9:], 'text': '', 'indicators': []}
            elif line.startswith('Text: '):
                current_tweet['text'] = line[6:]
            elif 'Promoted' in line or 'Sponsored' in line or 'Ad' in line:
                current_tweet['indicators'].append(line)

        if current_tweet:
            tweets.append(current_tweet)

        return tweets

    async def start_session(self):
        """Open browser and login to Twitter"""
        try:
            username = os.getenv("TWITTER_USERNAME")
            password = os.getenv("TWITTER_PASSWORD")

            if not username or not password:
                raise ValueError("TWITTER_USERNAME and TWITTER_PASSWORD must be set in environment variables")

            task = f"""
            Check login status and login if needed.

            STEP 1: Navigate to twitter.com and check if already logged in → VALIDATE: If homepage/timeline visible, IMMEDIATELY STOP (already logged in)

            If NOT logged in, continue with login:
            STEP 2: Click "Sign in" button → VALIDATE: Login form appears
            STEP 3: Type "{username}" → VALIDATE: Username entered
            STEP 4: Click "Next" button → VALIDATE: Password form appears
            STEP 5: Type "{password}" → VALIDATE: Password entered
            STEP 6: Click "Log in" button → VALIDATE: Home timeline loads

            IMMEDIATELY STOP when homepage is visible.
            """

            self.agent = Agent(
                task=task,
                llm=self.llm,
                browser_profile=self.safe_browser_profile,
                system_message="Check if logged in first. If already logged in, STOP immediately. If not, complete login then STOP.",
                max_steps=6,
                step_timeout=30,
                verbose=True
            )

            result = await self.agent.run()
            self.browser_session = self.agent.browser_session
            self.logged_in = True
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
            Post tweet in exactly 2 steps:

            STEP 1: Click compose button → VALIDATE: Tweet box opens
            STEP 2: Type "{text}" and click "Post" → VALIDATE: Tweet published

            STOP when tweet appears in timeline.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Post tweet in exactly 2 actions then STOP. Success = tweet appears in timeline.",
                max_steps=2,
                step_timeout=30,
                verbose=True
            )

            result = await agent.run()

            # Log tweet posting to memory
            interaction_data = {
                'type': 'tweet_post',
                'text': text,
                'author': 'self',
                'indicators': [],
                'success': True
            }
            self.memory_manager.log_interaction(interaction_data)

            # Update strategy effectiveness for posting
            self.memory_manager.update_strategy(
                'tweet_posting',
                True,
                {'content_type': 'original_tweet', 'text_length': len(text)}
            )

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
            Extract exactly {count} tweets from the current page in 1 action.

            Look at all visible tweets on the page and extract the first {count} different tweets you see.

            OUTPUT FORMAT (exactly {count} tweets):
            Author: @username
            Text: tweet content

            STOP immediately after extracting {count} tweets.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message=f"Extract exactly {count} tweets in 1 action then IMMEDIATELY STOP. Success = getting {count} different tweets.",
                max_steps=1,
                step_timeout=30,
                verbose=False
            )

            result = await agent.run()

            # Parse tweets and log to memory (excluding ads)
            tweets = self._parse_tweets_from_result(str(result))

            for tweet in tweets:
                interaction_data = {
                    'type': 'timeline_read',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'indicators': tweet.get('indicators', []),
                    'success': True
                }
                self.memory_manager.log_interaction(interaction_data)

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
            Get user tweets in exactly 2 steps:

            STEP 1: Navigate to "https://twitter.com/{username}" → VALIDATE: User profile loads
            STEP 2: Read {count} tweets from profile → VALIDATE: Tweet text extracted

            OUTPUT FORMAT:
            Author: @{username}
            Text: tweet content

            STOP after extracting visible tweets.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Get user tweets in exactly 2 actions then STOP. Success = reading tweets from user profile.",
                max_steps=2,
                step_timeout=30
            )

            result = await agent.run()

            # Parse tweets and log to memory (excluding ads)
            tweets = self._parse_tweets_from_result(str(result))
            for tweet in tweets:
                interaction_data = {
                    'type': 'user_tweets_read',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'indicators': tweet.get('indicators', []),
                    'success': True
                }
                self.memory_manager.log_interaction(interaction_data)

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
            Reply to tweet in exactly 2 steps:

            STEP 1: Navigate to: {tweet_url} → VALIDATE: Tweet page loads
            STEP 2: Click reply, type "{text}", send → VALIDATE: Reply posted

            STOP when reply appears under original tweet.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Reply to tweet in exactly 2 actions then STOP. Success = reply appears under original tweet.",
                max_steps=2,
                step_timeout=30
            )   

            result = await agent.run()

            # Log reply to memory
            interaction_data = {
                'type': 'tweet_reply',
                'text': text,
                'author': 'self',
                'indicators': [],
                'success': True,
                'tweet_url': tweet_url
            }
            self.memory_manager.log_interaction(interaction_data)

            # Update strategy effectiveness for replies
            self.memory_manager.update_strategy(
                'tweet_reply',
                True,
                {'content_type': 'reply', 'text_length': len(text), 'target_url': tweet_url}
            )

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
            Search Twitter in exactly 2 steps:

            STEP 1: Search for "{query}" → VALIDATE: Search results load
            STEP 2: Read {count} result tweets → VALIDATE: Tweet text extracted

            OUTPUT FORMAT:
            Author: @username
            Text: tweet content

            STOP after extracting search results.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Search Twitter in exactly 2 actions then STOP. Success = reading search result tweets.",
                max_steps=2,
                step_timeout=30
            )

            result = await agent.run()

            # Parse tweets and log to memory (excluding ads)
            tweets = self._parse_tweets_from_result(str(result))
            for tweet in tweets:
                interaction_data = {
                    'type': 'search_result',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'indicators': tweet.get('indicators', []),
                    'success': True,
                    'search_query': query
                }
                self.memory_manager.log_interaction(interaction_data)

            return result

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            raise

    def save_session(self):
        """Save browser state manually"""
        try:
            if not self.agent:
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
        except Exception as e:
            logger.error(f"Error closing session: {e}")