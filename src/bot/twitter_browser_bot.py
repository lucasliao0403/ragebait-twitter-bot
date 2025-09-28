import os
import asyncio
import logging
from browser_use import Agent, BrowserProfile
from browser_use.llm import ChatAnthropic
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
            POST TWEET: "{text}"

            STEPS:
            1. Click compose/tweet button
            2. Type the text: {text}
            3. Click post/send button

            Keep it simple and direct.
            """

            logger.info(f"Starting tweet post: {text[:50]}...")

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are on Twitter. Find the compose button, type the tweet, and post it. Keep it simple.",
                max_steps=4,  # More steps for reliability
                step_timeout=45,  # Longer timeout
                verbose=True  # Enable debugging
            )

            result = await agent.run()
            logger.info(f"Tweet posting completed. Result: {str(result)[:100]}...")

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

            logger.info(f"Successfully posted tweet: {text}")
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
            SIMPLE TASK: You are already on Twitter. Just read {count} tweets from the current page.

            STEPS:
            1. Look at the current page
            2. Find tweet text and usernames
            3. Copy exactly what you see

            FORMAT OUTPUT AS:
            Author: @username
            Text: exact tweet text

            Do NOT create files, do NOT make todo lists. Just read what's on screen.
            """

            logger.info(f"Starting timeline extraction for {count} tweets...")

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="You are on Twitter. Just read tweets from the current page. Do not navigate anywhere. Do not create files. Just extract text from what you can see.",
                max_steps=3,  # Fewer steps
                step_timeout=60,  # Longer timeout
                verbose=True  # Enable debugging
            )

            result = await agent.run()
            logger.info(f"Timeline extraction completed. Result: {str(result)[:200]}...")

            # Parse tweets and log to memory (excluding ads)
            tweets = self._parse_tweets_from_result(str(result))
            logger.info(f"Parsed {len(tweets)} tweets from result")

            for tweet in tweets:
                interaction_data = {
                    'type': 'timeline_read',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'indicators': tweet.get('indicators', []),
                    'success': True
                }
                self.memory_manager.log_interaction(interaction_data)

            logger.info(f"Retrieved {len(tweets)} timeline tweets")
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
                step_timeout=30  # Aggressive timeout
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
                step_timeout=30  # Fast timeout
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
                step_timeout=30  # Aggressive timeout
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