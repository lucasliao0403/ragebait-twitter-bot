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
        Add a tweet to DB.

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


def initialize_default_rag(db_path: str = None) -> StyleBasedRAG:
    """
    Initialize RAG system.

    Args:
        db_path: Path to persistent storage

    Returns:
        Initialized StyleBasedRAG instance
    """
    return StyleBasedRAG(db_path=db_path)
