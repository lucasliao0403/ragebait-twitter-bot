import os
import json
import logging
from typing import List, Dict
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 40  # Tweets per LLM query (optimal for Gemini 2.5 Flash Lite)


class TweetClassifier:
    """Classifies tweets using Gemini 2.5 Flash Lite to determine RAG-worthiness"""

    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - tweet classification will not work")
            self.enabled = False
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.enabled = True

        # Load classification prompt template
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'classification_prompt.txt')
        with open(prompt_path, 'r') as f:
            self.prompt_template = f.read()

        # Load reply classification prompt template
        reply_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'reply_classification_prompt.txt')
        with open(reply_prompt_path, 'r') as f:
            self.reply_prompt_template = f.read()

        logger.info("TweetClassifier initialized with Gemini 2.5 Flash Lite")

    def classify_batch(self, tweets: List[Dict[str, str]]) -> List[bool]:
        """
        Classify a batch of tweets.

        Args:
            tweets: List of tweet dicts with keys: 'text', 'author', 'url'

        Returns:
            List of booleans (True = accept to RAG, False = reject)
        """
        if not self.enabled:
            logger.warning("Classifier not enabled, accepting all tweets")
            return [True] * len(tweets)

        if not tweets:
            return []

        try:
            # Prepare tweets for classification (simplified format)
            tweets_for_llm = [
                {
                    "index": i,
                    "author": tweet.get('author', 'unknown'),
                    "text": tweet.get('text', '')
                }
                for i, tweet in enumerate(tweets)
            ]

            tweets_json = json.dumps(tweets_for_llm, indent=2)
            prompt = self.prompt_template.format(tweets_json=tweets_json)

            # Call Gemini
            logger.info(f"Classifying {len(tweets)} tweets with Gemini...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,  # Deterministic for classification
                    max_output_tokens=2000,
                )
            )

            # Parse response
            response_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                start = response_text.index('```json') + 7
                end = response_text.rindex('```')
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.index('```') + 3
                end = response_text.rindex('```')
                response_text = response_text[start:end].strip()

            result = json.loads(response_text)
            classifications = result.get('classifications', [])

            # Convert to boolean list
            accepts = [False] * len(tweets)
            for classification in classifications:
                idx = classification.get('index', -1)
                if 0 <= idx < len(tweets):
                    accepts[idx] = classification.get('accept', False)

                    # Log classification reasoning
                    if logger.isEnabledFor(logging.DEBUG):
                        reason = classification.get('reason', 'no reason')
                        status = "✓ ACCEPT" if accepts[idx] else "✗ REJECT"
                        logger.debug(f"{status} [{idx}] @{tweets[idx]['author']}: {reason}")

            accepted_count = sum(accepts)
            logger.info(f"Classification complete: {accepted_count}/{len(tweets)} accepted")

            return accepts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            # Fallback: accept all on parse error
            return [True] * len(tweets)

        except Exception as e:
            logger.error(f"Error classifying tweets: {e}")
            # Fallback: accept all on error
            return [True] * len(tweets)

    def classify_replies(self, original_tweet: Dict[str, str], replies: List[Dict[str, str]]) -> List[bool]:
        """
        Classify replies to a tweet for relevance and interestingness.

        Args:
            original_tweet: The original tweet dict with keys: 'text', 'author'
            replies: List of reply dicts with keys: 'text', 'author', 'url', 'engagement'

        Returns:
            List of booleans (True = accept, False = reject)
        """
        if not self.enabled:
            logger.warning("Classifier not enabled, accepting all replies")
            return [True] * len(replies)

        if not replies:
            return []

        try:
            # Prepare replies for classification
            replies_for_llm = [
                {
                    "index": i,
                    "author": reply.get('author', 'unknown'),
                    "text": reply.get('text', ''),
                    "engagement": reply.get('engagement', 0)
                }
                for i, reply in enumerate(replies)
            ]

            original_tweet_text = f"@{original_tweet.get('author', 'unknown')}: {original_tweet.get('text', '')}"
            replies_json = json.dumps(replies_for_llm, indent=2)
            prompt = self.reply_prompt_template.format(
                original_tweet=original_tweet_text,
                replies_json=replies_json
            )

            # Call Gemini
            logger.info(f"Classifying {len(replies)} replies with Gemini...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,  # Deterministic for classification
                    max_output_tokens=2000,
                )
            )

            # Parse response
            response_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                start = response_text.index('```json') + 7
                end = response_text.rindex('```')
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.index('```') + 3
                end = response_text.rindex('```')
                response_text = response_text[start:end].strip()

            result = json.loads(response_text)
            classifications = result.get('classifications', [])

            # Convert to boolean list
            accepts = [False] * len(replies)
            for classification in classifications:
                idx = classification.get('index', -1)
                if 0 <= idx < len(replies):
                    accepts[idx] = classification.get('accept', False)

                    # Log classification reasoning
                    if logger.isEnabledFor(logging.DEBUG):
                        reason = classification.get('reason', 'no reason')
                        status = "✓ ACCEPT" if accepts[idx] else "✗ REJECT"
                        logger.debug(f"{status} Reply[{idx}] @{replies[idx]['author']}: {reason}")

            accepted_count = sum(accepts)
            logger.info(f"Reply classification complete: {accepted_count}/{len(replies)} accepted")

            return accepts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            # Fallback: accept all on parse error
            return [True] * len(replies)

        except Exception as e:
            logger.error(f"Error classifying replies: {e}")
            # Fallback: accept all on error
            return [True] * len(replies)


async def classify_and_add_to_rag(
    tweets: List[Dict[str, str]],
    style_rag,
    batch_size: int = BATCH_SIZE
) -> tuple[int, List[Dict[str, str]]]:
    """
    Classify tweets in batches and add accepted ones to RAG database.

    Args:
        tweets: List of tweet dicts with keys: 'text', 'author', 'url'
        style_rag: StyleBasedRAG instance
        batch_size: Number of tweets per batch

    Returns:
        Tuple of (number of tweets added to RAG, list of accepted tweets)
    """
    if not tweets:
        return 0, []

    classifier = TweetClassifier()
    added_count = 0
    accepted_tweets = []

    # Process in batches
    for i in range(0, len(tweets), batch_size):
        batch = tweets[i:i + batch_size]
        accepts = classifier.classify_batch(batch)

        # Add accepted tweets to RAG
        for tweet, accept in zip(batch, accepts):
            if accept:
                try:
                    style_rag.add_style_tweet(
                        tweet=tweet['text'],
                        author=tweet['author'],
                        engagement=0,  # We don't have engagement data from timeline
                        category='auto_filtered',
                        url=tweet.get('url')
                    )
                    added_count += 1
                    accepted_tweets.append(tweet)
                    logger.debug(f"Added to RAG: @{tweet['author']}: {tweet['text'][:50]}...")
                except Exception as e:
                    logger.error(f"Failed to add tweet to RAG: {e}")

    logger.info(f"Auto-filtered: {added_count}/{len(tweets)} tweets added to RAG")
    return added_count, accepted_tweets
