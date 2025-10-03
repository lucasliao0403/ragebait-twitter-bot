import os
import asyncio
import logging
import json
from json import JSONDecoder
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

    def _parse_tweets_from_result(self, result):
        """Parse tweets from agent result - extract from final done action"""
        tweets = []

        print(f"\n[DEBUG] Result type: {type(result)}")

        # Get the final result text from AgentHistoryList
        content = None

        # Try to get final_result() method if it exists
        if hasattr(result, 'final_result'):
            try:
                final = result.final_result()
                print(f"[DEBUG] Got final_result: {str(final)[:200]}")
                content = str(final)
            except Exception as e:
                print(f"[DEBUG] Error calling final_result(): {e}")

        # Fallback: convert to string and extract JSON
        if content is None:
            content = str(result)
            print(f"[DEBUG] Using str(result)")

        # The result should contain a JSON array - find it
        if '[' in content and ']' in content:
            json_start = content.index('[')
            # Find the matching closing bracket
            json_end = content.rindex(']') + 1
            content = content[json_start:json_end]
            print(f"[DEBUG] Extracted JSON substring: {content[:200]}...")
        else:
            print(f"[DEBUG] WARNING: No JSON array found in result")
            return tweets

        try:
            # Parse the JSON using raw_decode to ignore trailing text
            json_data, _ = JSONDecoder().raw_decode(content)
            if isinstance(json_data, list):
                for tweet_data in json_data:
                    if isinstance(tweet_data, dict):
                        # Ensure all required fields exist with defaults
                        tweet = {
                            'author': str(tweet_data.get('author', '')).replace('@', ''),
                            'text': str(tweet_data.get('text', '')),
                            'url': str(tweet_data.get('url', ''))
                        }
                        # Only add tweet if it has content
                        if tweet['author'] and tweet['text']:
                            tweets.append(tweet)
            print(f"[DEBUG] JSON parsing successful: extracted {len(tweets)} tweets")
            return tweets

        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            logger.warning(f"JSON parsing failed: {e}, falling back to text parsing")
            print(f"[DEBUG] JSON parsing failed: {e}")
            # Fallback to text parsing for backwards compatibility
            lines = content.split('\n')
            current_tweet = {}

            for line in lines:
                line = line.strip()
                if line.startswith('Author: @'):
                    if current_tweet:
                        tweets.append(current_tweet)
                    current_tweet = {'author': line[9:], 'text': ''}
                elif line.startswith('Text: '):
                    current_tweet['text'] = line[6:]

            if current_tweet:
                tweets.append(current_tweet)

        print(f"[DEBUG] Text parsing completed: extracted {len(tweets)} tweets")
        if len(tweets) == 0:
            print(f"[DEBUG] WARNING: No tweets extracted! Check parsing logic.")
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
            STEP 2: Type "{text}" → VALIDATE: {text} entered
            STEP 3: Click "Post" button -> NO VALIDATION

            IMMEDIATELY STOP after step 2 no matter what.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message="Post tweet in exactly 3 actions then STOP.",
                max_steps=3,
                step_timeout=30,
                verbose=True
            )

            result = await agent.run()

            # Log tweet posting to memory
            interaction_data = {
                'type': 'tweet_post',
                'text': text,
                'author': 'self',
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
            Collect {count} tweets and return as JSON array.

            Step 1: Scroll down 2-3 times to load more tweets
            Step 2: Use extract_structured_data ONCE with query: "Return JSON array of {count} tweets: [{{"author": "@handle", "text": "content", "url": "tweet_link"}}]. Use the @handle (like @elonmusk), not the display name. Include the full tweet URL."
            Step 3: Call done with ONLY the JSON array, no text before or after

            Do NOT extract multiple times. Extract once after scrolling.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message=f"Scroll a few times, then extract {count} tweets ONCE, then call done. Do not extract multiple times.",
                max_steps=6,
                max_actions_per_step=1,
                step_timeout=30,
                verbose=False
            )

            result = await agent.run()

            # Parse tweets and log to memory
            tweets = self._parse_tweets_from_result(result)

            for tweet in tweets:
                interaction_data = {
                    'type': 'timeline_read',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'url': tweet.get('url', ''),
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

            # Parse tweets and log to memory
            tweets = self._parse_tweets_from_result(result)
            for tweet in tweets:
                interaction_data = {
                    'type': 'user_tweets_read',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
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
            STEP 2: Click "Post Your Reply" → VALIDATE: Reply box opens
            STEP 3: Type "{text}" → VALIDATE: {text} entered
            STEP 4: Click "Post" button → no validation.

            IMMEDIATELY STOP after step 4 no matter what.
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
            Search for "{query}" and collect {count} tweets as JSON array.

            Step 1: Search for "{query}" on Twitter
            Step 2: Scroll down 1-2 times to load more results
            Step 3: Use extract_structured_data ONCE with query: "Return JSON array of {count} tweets: [{{"author": "@handle", "text": "content", "url": "tweet_link"}}]. Use the @handle (like @elonmusk), not the display name. Include the full tweet URL."
            Step 4: Call done with ONLY the JSON array, no text before or after

            Do NOT extract multiple times. Extract once after scrolling.
            """

            agent = Agent(
                task=task,
                llm=self.llm,
                browser_session=self.browser_session,
                browser_profile=self.fast_browser_profile,
                system_message=f"Search for '{query}', scroll, then extract {count} tweets ONCE, then call done. Do not extract multiple times.",
                max_steps=6,
                max_actions_per_step=1,
                step_timeout=30,
                verbose=False
            )

            result = await agent.run()

            # Parse tweets and log to memory
            tweets = self._parse_tweets_from_result(result)
            for tweet in tweets:
                interaction_data = {
                    'type': 'search_result',
                    'text': tweet.get('text', ''),
                    'author': tweet.get('author', ''),
                    'url': tweet.get('url', ''),
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