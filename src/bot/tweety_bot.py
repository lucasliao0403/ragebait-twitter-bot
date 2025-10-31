import os
import logging
import re
import json
from dotenv import load_dotenv
from tweety import TwitterAsync
from anthropic import Anthropic
import google.generativeai as genai
from .memory_manager import MemoryManager
from .style_rag import initialize_default_rag
from .tone_modifiers import TONE_MODIFIERS

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose HTTP request logs from httpx/httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Constants
REPLIES_TO_FETCH = 10  # Number of replies to fetch per tweet

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

        # Initialize Gemini for tone classification
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            logger.warning("GEMINI_API_KEY not found - tone classification will fall back to default")
            self.gemini_enabled = False
        else:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            self.gemini_enabled = True
            logger.info("Gemini 2.5 Flash Lite initialized for tone classification")

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
            MAX_TWEETS_LIMIT = 2000
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

            # Filter boring tweets using LLM and add high-quality tweets to RAG
            if auto_add_to_rag and tweets:
                from .tweet_classifier import classify_and_add_to_rag, TweetClassifier
                added_count, accepted_tweets = await classify_and_add_to_rag(
                    tweets,
                    self.style_rag,
                    batch_size=40
                )
                if added_count > 0:
                    logger.info(f"🎯 Auto-added {added_count}/{len(tweets)} tweets to RAG database")

                # Fetch and filter replies for accepted tweets
                if accepted_tweets:
                    logger.info(f"Fetching replies for {len(accepted_tweets)} accepted tweets...")
                    classifier = TweetClassifier()
                    total_replies_fetched = 0
                    total_replies_stored = 0

                    for tweet in accepted_tweets:
                        try:
                            # Extract tweet ID from URL
                            tweet_id = tweet['url'].split('/')[-1]

                            # Fetch replies using tweety-ns API
                            logger.debug(f"Fetching replies for tweet {tweet_id}...")
                            comments = await self.client.get_tweet_comments(tweet_id, pages=1)

                            # Extract reply data from ConversationThread objects
                            replies_data = []
                            for thread in list(comments)[:REPLIES_TO_FETCH]:
                                # Each thread has a main tweet
                                if hasattr(thread, 'tweets') and thread.tweets:
                                    for reply_tweet in thread.tweets[:1]:  # Take first tweet from each thread
                                        if reply_tweet.id != tweet_id:  # Skip the original tweet
                                            reply_data = {
                                                'id': reply_tweet.id,
                                                'author': reply_tweet.author.username,
                                                'text': reply_tweet.text,
                                                'url': f"https://twitter.com/{reply_tweet.author.username}/status/{reply_tweet.id}",
                                                'engagement': (reply_tweet.likes or 0) + (reply_tweet.retweet_counts or 0)
                                            }
                                            replies_data.append(reply_data)

                            total_replies_fetched += len(replies_data)

                            if replies_data:
                                # Classify replies for relevance/interestingness
                                accepts = classifier.classify_replies(tweet, replies_data)

                                # Filter to only accepted replies
                                filtered_replies = [
                                    reply for reply, accept in zip(replies_data, accepts) if accept
                                ]

                                if filtered_replies:
                                    # Store in database
                                    self.memory_manager.log_replies(tweet['url'], filtered_replies)
                                    total_replies_stored += len(filtered_replies)

                                    # Add to RAG for style learning
                                    for reply in filtered_replies:
                                        try:
                                            self.style_rag.add_style_tweet(
                                                tweet=reply['text'],
                                                author=reply['author'],
                                                engagement=reply['engagement'],
                                                category='reply',
                                                url=reply.get('url')
                                            )
                                        except Exception as e:
                                            logger.error(f"Failed to add reply to RAG: {e}")

                        except Exception as e:
                            logger.error(f"Error fetching/processing replies for tweet {tweet.get('url', 'unknown')}: {e}")
                            continue

                    if total_replies_stored > 0:
                        logger.info(f"💬 Fetched {total_replies_fetched} replies, stored {total_replies_stored} filtered replies")

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

    def classify_tone(self, original_tweet_text: str, original_author: str, previous_tweets: list, reply_context: str) -> dict:
        """
        Classify the optimal tone for replying to a tweet using Gemini Flash.

        Args:
            original_tweet_text: The tweet being replied to
            original_author: Username of the tweet author
            previous_tweets: List of previous tweets from this author
            reply_context: Formatted reply examples from similar tweets

        Returns:
            Dict with 'tone' (supportive/ragebait/funny) and 'reasoning'
        """
        try:
            # Read tone classifier prompt
            classifier_prompt_path = os.path.join(os.path.dirname(__file__), 'tone_classifier_prompt.txt')
            with open(classifier_prompt_path, 'r') as f:
                classifier_system_prompt = f.read().strip()

            # Build context for tone classifier
            context_parts = [
                classifier_system_prompt,
                "",
                "="*70,
                "CONTEXT TO ANALYZE:",
                "="*70,
                "",
                f"ORIGINAL TWEET:",
                f"Author: @{original_author}",
                f'Text: "{original_tweet_text}"',
                ""
            ]

            if previous_tweets:
                context_parts.append("AUTHOR'S PREVIOUS TWEETS (their typical style):")
                for i, tweet in enumerate(previous_tweets[:5], 1):
                    context_parts.append(f"{i}. {tweet}")
                context_parts.append("")

            if reply_context:
                context_parts.append(reply_context)
                context_parts.append("")

            context_parts.append("Based on all this context, what tone should the reply use?")
            context_parts.append("Output ONLY the JSON object, no other text.")

            full_prompt = "\n".join(context_parts)

            # Call Gemini for tone classification
            logger.info("Classifying optimal reply tone with Gemini Flash...")

            if not self.gemini_enabled:
                logger.warning("Gemini not enabled, falling back to contrarian")
                return {
                    "tone": "contrarian",
                    "reasoning": "Gemini not configured, using default contrarian tone"
                }

            logger.info(f"Full tone classifier prompt:\n{full_prompt}")

            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low temperature for consistent classification
                    max_output_tokens=300,
                ),
                safety_settings=[
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE
                    ),
                ]
            )

            # Check for safety blocks or empty response
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.warning(f"Gemini blocked response (finish_reason={finish_reason}), falling back to contrarian")
                return {
                    "tone": "contrarian",
                    "reasoning": f"Gemini safety filter triggered (reason: {finish_reason}), using default tone"
                }

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON if wrapped in markdown
            if "```json" in response_text:
                json_start = response_text.index("```json") + 7
                json_end = response_text.index("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.index("```") + 3
                json_end = response_text.index("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            tone_data = json.loads(response_text)

            logger.info(f"✓ Classified tone as '{tone_data['tone']}': {tone_data['reasoning']}")
            return tone_data

        except Exception as e:
            logger.error(f"Error classifying tone: {e}")
            # Fallback to contrarian (your current default)
            logger.warning("Falling back to 'contrarian' tone")
            return {
                "tone": "contrarian",
                "reasoning": "Error during classification, using default contrarian tone"
            }

    def get_reply_style_context(self, original_tweet_text: str, n: int = 5):
        """
        Get reply style context using two-step process:
        1. Find similar original tweets in ChromaDB
        2. Get replies to those tweets from SQL database

        Args:
            original_tweet_text: The tweet being replied to
            n: Number of similar tweets to find

        Returns:
            Formatted string with reply examples for the LLM prompt
        """
        try:
            # Step 1: Query ChromaDB for similar original tweets (not replies)
            logger.info("Querying ChromaDB for similar original tweets...")
            results = self.style_rag.query_similar_tweets(
                original_tweet_text,
                n=n,
                category='auto_filtered'
            )

            if not results or not results.get('metadatas') or not results['metadatas'][0]:
                logger.warning("No similar original tweets found in RAG")
                return ""

            # Step 2: Extract tweet URLs from results
            tweet_urls = []
            for metadata in results['metadatas'][0]:
                url = metadata.get('url')
                if url:
                    tweet_urls.append(url)

            if not tweet_urls:
                logger.warning("No tweet URLs found in RAG metadata")
                return ""

            logger.info(f"Found {len(tweet_urls)} similar tweets, fetching their replies...")

            # Step 3: Build tweet + replies pairs
            tweet_reply_pairs = []
            for i, metadata in enumerate(results['metadatas'][0]):
                url = metadata.get('url')
                if not url:
                    continue

                # Get the original tweet text
                original_tweet_text = results['documents'][0][i]
                original_author = metadata.get('author', 'unknown')

                # Get replies from SQL
                replies = self.memory_manager.get_replies(url)
                if replies:
                    # Sort by engagement
                    sorted_replies = sorted(replies, key=lambda r: r.get('engagement', 0), reverse=True)
                    tweet_reply_pairs.append({
                        'original_tweet': original_tweet_text,
                        'original_author': original_author,
                        'replies': sorted_replies[:5]  # Top 5 replies per tweet
                    })

            if not tweet_reply_pairs:
                logger.warning("No replies found for similar tweets")
                return ""

            # Step 4: Format as tweet + replies examples
            reply_context = "REPLY STYLE REFERENCE (study how these replies engage with similar tweets):\n\n"

            for i, pair in enumerate(tweet_reply_pairs[:3], 1):  # Show top 3 tweet+reply groups
                reply_context += f"EXAMPLE {i}:\n"
                reply_context += f"Original Tweet by @{pair['original_author']}:\n"
                reply_context += f'"{pair["original_tweet"]}"\n\n'
                reply_context += "Replies:\n"

                for j, reply in enumerate(pair['replies'], 1):
                    author = reply.get('author', 'unknown')
                    text = reply.get('text', '')
                    engagement = reply.get('engagement', 0)
                    reply_context += f"  {j}. @{author} ({engagement} engagement): \"{text}\"\n"

                reply_context += "\n"

            reply_context += "💡 Notice how replies engage with the original tweet's topic and tone"

            total_replies = sum(len(pair['replies']) for pair in tweet_reply_pairs[:3])
            logger.info(f"Retrieved {len(tweet_reply_pairs[:3])} tweet+reply examples with {total_replies} total replies")
            # logger.info(f"Reply context:\n{reply_context}")
            return reply_context

        except Exception as e:
            logger.error(f"Failed to get reply style context: {e}")
            return ""  # Graceful degradation

    async def generate_reply(self, tweet_url):
        """Generate an AI reply to a tweet using Claude"""
        if not self.logged_in:
            raise Exception("Not logged in. Call start_session() first.")

        try:
            # Extract tweet ID and fetch tweet details
            tweet_id = self._extract_tweet_id_from_url(tweet_url)
            logger.info(f"Fetching tweet details for ID: {tweet_id}")

            tweet = await self.client.tweet_detail(tweet_id)
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

            # Get reply examples from similar tweets (two-step: ChromaDB → SQL)
            reply_context = self.get_reply_style_context(original_text, n=5)
            if reply_context:
                context_parts.append(f"\n{reply_context}")

            # Classify tone based on all context
            tone_data = self.classify_tone(
                original_tweet_text=original_text,
                original_author=original_author,
                previous_tweets=previous_tweets,
                reply_context=reply_context
            )

            # Get the appropriate tone modifier
            tone = tone_data.get('tone', 'contrarian')
            tone_modifier = TONE_MODIFIERS.get(tone, TONE_MODIFIERS['contrarian'])

            # Add tone-specific instructions
            context_parts.append(f"\n{tone_modifier}")

            context_parts.append("\nGenerate a reply tweet (max 280 characters).")
            context_parts.append("\nRespond with ONLY the tweet text, nothing else.")

            user_prompt = "\n".join(context_parts)

            # Call Claude
            response = self.anthropic.messages.create(
                model="claude-opus-4-1",
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
