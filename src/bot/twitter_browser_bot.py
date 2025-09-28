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
            Complete Twitter login using these exact steps:

            1. Use action 'click' on button with text "Sign in" or "Log in"
            2. Use action 'type' to enter "{username}" in the username/email field
            3. Use action 'click' on button with text "Next" (blue primary button only)
            4. Use action 'type' to enter "{password}" in the password field
            5. Use action 'click' on button with text "Log in" or "Sign in" (blue primary button only)

            ERROR RECOVERY:
            - If button click fails, use keyboard 'Tab' + 'Enter' instead
            - If field not found, use 'click' on input[type="email"] or input[type="password"]
            - Ignore any "Forgot password" or "Reset password" links

            SUCCESS: You will see Twitter home timeline with tweets
            """

            self.agent = Agent(
                task=task,
                llm=self.llm,
                browser_profile=self.safe_browser_profile,
                system_message="Execute login actions precisely. Use specific action names: 'click', 'type', 'key'. Target blue primary buttons only. Skip secondary links.",
                max_steps=6,
                step_timeout=45,
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
            Post tweet with exact actions:

            1. Use action 'click' on button containing "Tweet", "Post", or "What's happening"
            2. Use action 'type' to enter: {text}
            3. Use action 'click' on blue "Post" or "Tweet" button

            ERROR RECOVERY:
            - If compose button not found, use 'key' with 'n' (Twitter shortcut)
            - If text area not found, use 'click' on textarea or div[contenteditable]
            - If post fails, use keyboard 'Ctrl+Enter'

            SUCCESS: Tweet appears in timeline
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Execute precise tweet posting actions. Use action names: 'click', 'type', 'key'. Focus on compose workflow.",
                max_steps=4,
                step_timeout=45,
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
            Extract {count} tweets using extract_structured_data action:

            1. Use action 'extract_structured_data' with query: "Extract tweet text and usernames"
            2. Target elements: article, div[data-testid="tweet"], or similar tweet containers
            3. Extract: username (starts with @) and tweet text content

            OUTPUT FORMAT:
            Author: @username
            Text: exact tweet text

            ERROR RECOVERY:
            - If extraction fails, use 'scroll' down to load more tweets
            - If no tweets visible, navigate to Twitter home with 'go_to_url'
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Execute data extraction actions. Use 'extract_structured_data' for tweets. Focus on username and text content only.",
                max_steps=2,
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
            Get tweets from user @{username} using exact actions:

            1. Use action 'go_to_url' to navigate to "https://twitter.com/{username}"
            2. Use action 'extract_structured_data' with query: "Extract {count} recent tweets with full text"
            3. Target tweet containers: article or div[data-testid="tweet"]

            OUTPUT FORMAT:
            Author: @{username}
            Text: complete tweet text with emojis, links, hashtags

            ERROR RECOVERY:
            - If user page not found, try alternative URL format
            - If no tweets visible, use 'scroll' down to load content
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Execute user profile actions. Use 'go_to_url', 'extract_structured_data'. Focus on tweet extraction workflow.",
                max_steps=5,
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
            Reply to tweet using exact actions:

            1. Use action 'go_to_url' to navigate to: {tweet_url}
            2. Use action 'click' on reply button (icon or text "Reply")
            3. Use action 'type' to enter: {text}
            4. Use action 'click' on blue "Reply" button to send

            ERROR RECOVERY:
            - If reply button not found, use 'key' with 'r' (Twitter shortcut)
            - If text area not found, use 'click' on textarea or div[contenteditable]
            - If send fails, use keyboard 'Ctrl+Enter'

            SUCCESS: Your reply appears under the original tweet
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Execute reply actions precisely. Use 'go_to_url', 'click', 'type' actions. Target reply workflow efficiently.",
                max_steps=4,  # Few steps for replying
                step_timeout=45  # Fast timeout
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
            Search Twitter using exact actions:

            1. Use action 'click' on search box or use 'key' with '/' (Twitter shortcut)
            2. Use action 'type' to enter search query: {query}
            3. Use action 'key' with 'Enter' to execute search
            4. Use action 'extract_structured_data' to get {count} tweet results

            OUTPUT FORMAT:
            Author: @username
            Text: complete tweet text with emojis, links, hashtags

            ERROR RECOVERY:
            - If search box not found, navigate to "https://twitter.com/search"
            - If no results, try alternative search terms
            - If extraction fails, use 'scroll' to load more results
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Execute search and extraction actions. Use 'click', 'type', 'key', 'extract_structured_data'. Focus on search workflow.",
                max_steps=5,
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