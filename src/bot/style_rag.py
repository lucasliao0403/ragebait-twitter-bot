import os
import chromadb
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class StyleBasedRAG:
    """
    RAG system that learns writing style from example tweets.
    Stores tweets from accounts with the right vibe, retrieves similar ones
    to guide reply generation.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the RAG system.

        Args:
            db_path: Path to ChromaDB storage. If None, uses in-memory storage.
        """
        if db_path:
            self.client = chromadb.PersistentClient(path=db_path)
        else:
            self.client = chromadb.Client()

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="tech_twitter_style",
            metadata={"description": "Tweets that exemplify the right tech Twitter vibe"}
        )

        # Initialize OpenAI for embeddings
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.openai = OpenAI(api_key=api_key)

        logger.info(f"StyleBasedRAG initialized with {self.collection.count()} style tweets")

    def add_style_tweet(self, tweet: str, author: str, engagement: int = 0, category: str = None):
        """
        Add a tweet that exemplifies the vibe you want.

        Args:
            tweet: The tweet text
            author: Twitter handle (without @)
            engagement: Number of likes/retweets (optional, for filtering later)
            category: Optional category like 'hot_take', 'joke', 'advice'
        """
        try:
            # Create embedding
            embedding = self.openai.embeddings.create(
                input=tweet,
                model="text-embedding-3-small"
            ).data[0].embedding

            # Prepare metadata
            metadata = {
                'author': author,
                'engagement': engagement,
                'length': len(tweet.split()),
                'is_lowercase': tweet.islower(),
            }
            if category:
                metadata['category'] = category

            # Generate unique ID
            tweet_id = f"{author}_{hash(tweet)}"

            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[tweet],
                metadatas=[metadata],
                ids=[tweet_id]
            )

            logger.info(f"Added style tweet from @{author}: {tweet[:50]}...")

        except Exception as e:
            logger.error(f"Failed to add style tweet: {e}")
            raise

    def add_bulk_style_tweets(self, tweets: list[dict]):
        """
        Add multiple style tweets at once.

        Args:
            tweets: List of dicts with keys: 'text', 'author', 'engagement' (optional), 'category' (optional)
        """
        for tweet_data in tweets:
            self.add_style_tweet(
                tweet=tweet_data['text'],
                author=tweet_data['author'],
                engagement=tweet_data.get('engagement', 0),
                category=tweet_data.get('category')
            )

        logger.info(f"Added {len(tweets)} style tweets in bulk")

    def get_style_context(self, original_tweet: str, n: int = 5):
        """
        Get similar tweets from people with the right vibe.

        Args:
            original_tweet: The tweet to reply to
            n: Number of similar style tweets to retrieve

        Returns:
            Formatted string with style examples for the LLM prompt
        """
        try:
            # Create embedding for query
            query_embedding = self.openai.embeddings.create(
                input=original_tweet,
                model="text-embedding-3-small"
            ).data[0].embedding

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n
            )

            # Check if we got results
            if not results['documents'] or not results['documents'][0]:
                logger.warning("No style tweets found in RAG")
                return ""

            # Format for prompt
            style_context = "VOICE REFERENCE (match this casual, brief tech Twitter style):\n\n"

            for i in range(len(results['documents'][0])):
                author = results['metadatas'][0][i]['author']
                tweet = results['documents'][0][i]
                length = results['metadatas'][0][i]['length']

                style_context += f"@{author}: \"{tweet}\" ({length} words)\n"

            style_context += "\n💡 Notice: brevity, lowercase, natural voice, effortless wit"
            logger.info(f"Retrieved {len(results['documents'][0])} style tweets for context")
            logger.info(f"Style context: {style_context}")


            return style_context

        except Exception as e:
            logger.error(f"Failed to get style context: {e}")
            return ""  # Graceful degradation - continue without RAG

    def count(self) -> int:
        """Return number of style tweets in database"""
        return self.collection.count()

    def clear(self):
        """Clear all style tweets from database"""
        self.client.delete_collection("tech_twitter_style")
        self.collection = self.client.create_collection("tech_twitter_style")
        logger.info("Cleared all style tweets from RAG")


# Starter dataset - curated tech Twitter examples
STARTER_STYLE_TWEETS = [
    # Sam Altman - brief wisdom
    {'text': 'the right amount of crazy is a lot', 'author': 'sama', 'engagement': 2500, 'category': 'advice'},
    {'text': 'startups are a game of people', 'author': 'sama', 'engagement': 1800, 'category': 'advice'},
    {'text': 'most advice is autobiographical', 'author': 'sama', 'engagement': 3200, 'category': 'observation'},
    {'text': 'ideas are easy execution is everything', 'author': 'sama', 'engagement': 1500, 'category': 'advice'},

    # Andrej Karpathy - technical but accessible
    {'text': 'llms are calculators for words', 'author': 'karpathy', 'engagement': 5000, 'category': 'observation'},
    {'text': 'reading papers is underrated', 'author': 'karpathy', 'engagement': 1200, 'category': 'advice'},
    {'text': 'just ship it and iterate', 'author': 'karpathy', 'engagement': 2100, 'category': 'advice'},
    {'text': 'debugging is half the job', 'author': 'karpathy', 'engagement': 900, 'category': 'observation'},

    # Paul Graham - philosophical
    {'text': 'do things that dont scale', 'author': 'paulg', 'engagement': 4500, 'category': 'advice'},
    {'text': 'write like you talk', 'author': 'paulg', 'engagement': 2800, 'category': 'advice'},
    {'text': 'make something people want', 'author': 'paulg', 'engagement': 3500, 'category': 'advice'},

    # Pieter Levels - builder vibe
    {'text': 'just fucking build it', 'author': 'levelsio', 'engagement': 6000, 'category': 'advice'},
    {'text': 'ship fast break things', 'author': 'levelsio', 'engagement': 2300, 'category': 'advice'},
    {'text': 'your mvp is too complex', 'author': 'levelsio', 'engagement': 1900, 'category': 'observation'},

    # John Carmack - deep tech casual
    {'text': 'measure dont guess', 'author': 'ID_AA_Carmack', 'engagement': 1500, 'category': 'advice'},
    {'text': 'premature optimization is real', 'author': 'ID_AA_Carmack', 'engagement': 2200, 'category': 'observation'},

    # Naval - concise wisdom
    {'text': 'specific knowledge is wealth', 'author': 'naval', 'engagement': 8000, 'category': 'observation'},
    {'text': 'leverage is how you get rich', 'author': 'naval', 'engagement': 5500, 'category': 'advice'},

    # Patrick McKenzie - practical
    {'text': 'charge more', 'author': 'patio11', 'engagement': 3200, 'category': 'advice'},
    {'text': 'talk to your customers', 'author': 'patio11', 'engagement': 1800, 'category': 'advice'},

    # Casual tech Twitter vibe
    {'text': 'this is so unhinged lmao', 'author': 'various', 'engagement': 500, 'category': 'reaction'},
    {'text': 'cant believe this is real', 'author': 'various', 'engagement': 450, 'category': 'reaction'},
    {'text': 'based take tbh', 'author': 'various', 'engagement': 600, 'category': 'reaction'},
    {'text': 'worked for zuck', 'author': 'various', 'engagement': 1200, 'category': 'callback'},
    {'text': 'vibes check passed', 'author': 'various', 'engagement': 400, 'category': 'reaction'},
]


def initialize_default_rag(db_path: str = None) -> StyleBasedRAG:
    """
    Initialize RAG with starter dataset if empty.

    Args:
        db_path: Path to persistent storage

    Returns:
        Initialized StyleBasedRAG instance
    """
    rag = StyleBasedRAG(db_path=db_path)

    # Add starter tweets if database is empty
    if rag.count() == 0:
        logger.info("RAG database empty, adding starter dataset...")
        rag.add_bulk_style_tweets(STARTER_STYLE_TWEETS)
        logger.info(f"Added {len(STARTER_STYLE_TWEETS)} starter style tweets")

    return rag
