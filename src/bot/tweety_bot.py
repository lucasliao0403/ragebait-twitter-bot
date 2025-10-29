import os
import logging
import re
from dotenv import load_dotenv
from tweety import TwitterAsync
from anthropic import Anthropic
from .memory_manager import MemoryManager
from .style_rag import initialize_default_rag

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose HTTP request logs from httpx/httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class TweetyBot:
    def __init__(self):
        self.client = TwitterAsync("twitter_session")
        self.logged_in = False
        self.memory_manager = MemoryManager()

        # init RAG system
        rag_db_path = os.path.join(os.getcwd(), '.rag_data')
        self.style_rag = initialize_default_rag(db_path=rag_db_path)

        # init anthropic client
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not found - AI reply generation will not work")
        self.anthropic = Anthropic(api_key=anthropic_api_key)

    def _extract_tweet_id_from_url(self, url: str) -> str:
        """Extract tweet ID from Twitter URL"""
        # URL format: https://twitter.com/username/status/1234567890
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract tweet ID from URL: {url}")

    def _extract_username_from_url(self, url: str) -> str:
        """Extract username from Twitter URL"""
        match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status/', url)
        if match:
            return match.group(1)
        return 'unknown'

    async def start_session(self):
        """Authenticate with Twitter using session ID"""
        try:
            session_id = os.getenv("TWITTER_SESSION_ID")

            if not session_id:
                raise ValueError("TWITTER_SESSION_ID must be set in environment variables")

            logger.info("Attempting to authenticate with session ID...")
            await self.client.load_auth_token(session_id)
            self.logged_in = True
            logger.info("✓ Logged in using session ID")

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise

    async def post_tweet(self, text):
        """Post a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            logger.info(f"Posting tweet: {text[:50]}...")
            tweet = await self.client.create_tweet(text)

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

            logger.info("✓ Tweet posted successfully")
            return tweet

        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            raise

    async def get_timeline(self, count=10, auto_add_to_rag=True):
        """Read home timeline and optionally auto-filter tweets to RAG"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            logger.info(f"Fetching {count} tweets from timeline...")

            # Fetch tweets using cursor-based pagination
            tweets = []
            cursor = None
            batch_count = 0
            MAX_TWEETS_LIMIT = 600
            max_batches = MAX_TWEETS_LIMIT // 20  # Safety limit (30 batches * ~20 tweets = 600 max)

            while len(tweets) < count and batch_count < max_batches:
                # Fetch batch using cursor parameter (tweety-ns pagination)
                timeline = await self.client.get_home_timeline(pages=1, cursor=cursor)

                # Convert to list if iterator
                batch = list(timeline) if hasattr(timeline, '__iter__') else []

                if not batch:
                    logger.info(f"Timeline exhausted after {len(tweets)} tweets")
                    break

                # Process each tweet in batch
                for tweet in batch:
                    if len(tweets) >= count:
                        break

                    tweet_data = {
                        'author': tweet.author.username,
                        'text': tweet.text,
                        'url': f"https://twitter.com/{tweet.author.username}/status/{tweet.id}"
                    }
                    tweets.append(tweet_data)

                    # Log to memory
                    interaction_data = {
                        'type': 'timeline_read',
                        'text': tweet.text,
                        'author': tweet.author.username,
                        'url': tweet_data['url'],
                        'success': True
                    }
                    self.memory_manager.log_interaction(interaction_data)

                # Extract cursor for next batch from SelfTimeline object
                # Try common attribute names for pagination cursor
                if hasattr(timeline, 'cursor'):
                    cursor = timeline.cursor
                elif hasattr(timeline, 'next_cursor'):
                    cursor = timeline.next_cursor
                else:
                    # If cursor attribute not found, cannot paginate further
                    logger.warning(f"Could not find cursor on SelfTimeline object after batch {batch_count}, stopping pagination")
                    break

                # Stop if cursor is None (no more pages)
                if cursor is None:
                    logger.info(f"No more pages available after {len(tweets)} tweets")
                    break

                batch_count += 1

            logger.info(f"✓ Fetched {len(tweets)} tweets from timeline in {batch_count} batch(es)")

            # Auto-filter and add high-quality tweets to RAG
            if auto_add_to_rag and tweets:
                from .tweet_classifier import classify_and_add_to_rag
                added_count = await classify_and_add_to_rag(
                    tweets,
                    self.style_rag,
                    batch_size=40
                )
                if added_count > 0:
                    logger.info(f"🎯 Auto-added {added_count}/{len(tweets)} tweets to RAG database")

            return tweets

        except Exception as e:
            logger.error(f"Error getting timeline: {e}")
            raise

    async def get_user_tweets(self, username, count=10):
        """Get specific user's tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            logger.info(f"Fetching {count} tweets from @{username}...")

            # Get user tweets
            user_tweets = await self.client.get_tweets(username)

            tweets = []
            for tweet in user_tweets[:count]:
                tweet_data = {
                    'author': username,
                    'text': tweet.text,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}"
                }
                tweets.append(tweet_data)

                # Log to memory
                interaction_data = {
                    'type': 'user_tweets_read',
                    'text': tweet.text,
                    'author': username,
                    'url': tweet_data['url'],
                    'success': True
                }
                self.memory_manager.log_interaction(interaction_data)

            logger.info(f"✓ Fetched {len(tweets)} tweets from @{username}")
            return tweets

        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
            raise

    async def generate_reply(self, tweet_url):
        """Generate an AI reply to a tweet using Claude"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Extract tweet ID and fetch tweet details
            tweet_id = self._extract_tweet_id_from_url(tweet_url)
            logger.info(f"Fetching tweet details for ID: {tweet_id}")

            tweet = await self.client.get_tweet_detail(tweet_id)
            original_author = tweet.author.username
            original_text = tweet.text

            logger.info(f"Generating reply to @{original_author}: {original_text[:50]}...")

            # Get previous tweets by this author from memory
            import sqlite3
            db_conn = sqlite3.connect(self.memory_manager.db_path)
            db_conn.row_factory = sqlite3.Row
            cursor = db_conn.cursor()

            cursor.execute('''
                SELECT content FROM interactions
                WHERE author = ? AND type IN ('timeline_read', 'search_result', 'user_tweets_read')
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (original_author,))

            previous_tweets = [dict(row)['content'] for row in cursor.fetchall()]
            db_conn.close()

            # Read system prompt
            system_prompt_path = os.path.join(os.path.dirname(__file__), 'reply_prompt.txt')
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read().strip()

            # Build context for Claude
            context_parts = [
                f"You are replying to this tweet from @{original_author}:",
                f"\"{original_text}\"",
                f"\nTweet URL: {tweet_url}",
            ]

            if previous_tweets:
                context_parts.append(f"\nPrevious tweets from @{original_author} (for style reference):")
                for i, tweet in enumerate(previous_tweets[:5], 1):
                    context_parts.append(f"{i}. {tweet}")

            # Get style examples from RAG
            style_context = self.style_rag.get_style_context(original_text, n=8)
            if style_context:
                context_parts.append(f"\n{style_context}")

            context_parts.append("\nGenerate a reply tweet (max 280 characters) that:")
            context_parts.append("- Engages with the original tweet's context")
            context_parts.append("- Creates maximum engagement (controversy, hot takes, ragebait)")
            context_parts.append("- Matches tech bro energy")
            context_parts.append("- Is designed to get replies/quote tweets")
            context_parts.append("\nRespond with ONLY the tweet text, nothing else.")

            user_prompt = "\n".join(context_parts)

            # Call Claude
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=150,
                temperature=1.0,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            generated_reply = response.content[0].text.strip()

            # Remove quotes if Claude wrapped the response
            if generated_reply.startswith('"') and generated_reply.endswith('"'):
                generated_reply = generated_reply[1:-1]

            logger.info(f"Generated reply: {generated_reply}")

            return generated_reply

        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            raise

    async def reply_to_tweet(self, tweet_url, text):
        """Reply to a tweet"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Extract tweet ID from URL
            tweet_id = self._extract_tweet_id_from_url(tweet_url)
            author = self._extract_username_from_url(tweet_url)

            logger.info(f"Replying to tweet {tweet_id}: {text[:50]}...")

            # Create reply
            tweet = await self.client.create_tweet(text, reply_to=tweet_id)

            # Log reply to memory
            interaction_data = {
                'type': 'tweet_reply',
                'text': text,
                'author': 'self',
                'tweet_url': tweet_url
            }
            self.memory_manager.log_interaction(interaction_data)

            # Log conversation (thread_id is the tweet URL)
            self.memory_manager.log_conversation(
                thread_id=tweet_url,
                original_tweet={'url': tweet_url, 'author': author},
                reply_tweet={'text': text}
            )

            # Update strategy effectiveness for replies
            self.memory_manager.update_strategy(
                'tweet_reply',
                True,
                {'content_type': 'reply', 'text_length': len(text), 'target_url': tweet_url}
            )

            logger.info("✓ Reply posted successfully")
            return tweet

        except Exception as e:
            logger.error(f"Error replying to tweet: {e}")
            raise

    async def search_tweets(self, query, count=10):
        """Search for tweets"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            logger.info(f"Searching for '{query}'...")

            # Search tweets
            from tweety.filters import SearchFilters
            search_results = await self.client.search(query, filter_=SearchFilters.Latest())

            tweets = []
            for tweet in search_results[:count]:
                tweet_data = {
                    'author': tweet.author.username,
                    'text': tweet.text,
                    'url': f"https://twitter.com/{tweet.author.username}/status/{tweet.id}"
                }
                tweets.append(tweet_data)

                # Log to memory
                interaction_data = {
                    'type': 'search_result',
                    'text': tweet.text,
                    'author': tweet.author.username,
                    'url': tweet_data['url'],
                    'success': True,
                    'search_query': query
                }
                self.memory_manager.log_interaction(interaction_data)

            logger.info(f"✓ Found {len(tweets)} tweets for '{query}'")
            return tweets

        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            raise

    async def close_session(self):
        """Close session (cleanup)"""
        try:
            # tweety-ns saves session automatically, just set logged_in to False
            self.logged_in = False
            logger.info("✓ Session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")
