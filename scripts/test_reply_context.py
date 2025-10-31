#!/usr/bin/env python3
"""
Test script for the reply context retrieval (two-step: ChromaDB → SQL).
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.style_rag import initialize_default_rag
from src.memory_manager import MemoryManager

def test_two_step_query():
    """Test the two-step query process"""
    print("\n" + "="*70)
    print("Testing Two-Step Reply Context Retrieval")
    print("="*70)

    # Initialize components
    print("\n1. Initializing components...")
    rag = initialize_default_rag(db_path='.rag_data')
    mm = MemoryManager()

    print(f"   ChromaDB tweets: {rag.count()}")

    # Check replies table
    replies = mm.get_replies("")  # Try to get any replies
    print(f"   SQL replies table: Ready")

    # Test query_similar_tweets method
    print("\n2. Testing query_similar_tweets() with category filter...")
    test_query = "building AI applications"

    results = rag.query_similar_tweets(
        query_text=test_query,
        n=3,
        category='auto_filtered'
    )

    if results and results.get('metadatas') and results['metadatas'][0]:
        print(f"   ✓ Found {len(results['metadatas'][0])} similar original tweets")

        for i, metadata in enumerate(results['metadatas'][0], 1):
            print(f"\n   Tweet {i}:")
            print(f"     Author: @{metadata.get('author', 'unknown')}")
            print(f"     Category: {metadata.get('category', 'N/A')}")
            print(f"     URL: {metadata.get('url', 'N/A')}")
            print(f"     Text: {results['documents'][0][i-1][:60]}...")

            # Check if this tweet has replies
            if metadata.get('url'):
                tweet_replies = mm.get_replies(metadata['url'])
                print(f"     Replies: {len(tweet_replies)}")
    else:
        print("   ⚠️  No similar tweets found")
        print("   Make sure you've run timeline reading with auto_add_to_rag=True")
        return False

    # Test the full two-step process (simulating what happens in generate_reply)
    print("\n3. Testing full two-step process...")
    print(f"   Query: '{test_query}'")

    # Step 1: Find similar original tweets
    results = rag.query_similar_tweets(
        query_text=test_query,
        n=5,
        category='auto_filtered'
    )

    if not results or not results.get('metadatas') or not results['metadatas'][0]:
        print("   ⚠️  No similar tweets found")
        return False

    # Step 2: Get tweet URLs
    tweet_urls = []
    for metadata in results['metadatas'][0]:
        url = metadata.get('url')
        if url:
            tweet_urls.append(url)

    print(f"   Found {len(tweet_urls)} tweet URLs")

    # Step 3: Get replies from SQL
    all_replies = []
    for tweet_url in tweet_urls:
        replies = mm.get_replies(tweet_url)
        all_replies.extend(replies)
        if replies:
            print(f"   - {tweet_url}: {len(replies)} replies")

    print(f"\n   Total replies found: {len(all_replies)}")

    if all_replies:
        print("\n   Sample replies:")
        sorted_replies = sorted(all_replies, key=lambda r: r.get('engagement', 0), reverse=True)
        for i, reply in enumerate(sorted_replies[:3], 1):
            print(f"\n   {i}. @{reply.get('author', 'unknown')} (engagement: {reply.get('engagement', 0)})")
            print(f"      {reply.get('text', '')[:80]}...")

        print("\n   ✓ Two-step process working correctly!")
        return True
    else:
        print("\n   ⚠️  No replies found for similar tweets")
        print("   This could mean:")
        print("   - The tweets in ChromaDB don't have replies yet")
        print("   - The tweets were added before reply fetching was implemented")
        print("   - Run timeline reading again to fetch replies")
        return False

def main():
    """Run test"""
    try:
        success = test_two_step_query()

        print("\n" + "="*70)
        if success:
            print("✅ TEST PASSED: Reply context retrieval is working!")
            print("\nThe system will now:")
            print("1. Find tweets similar to the one you're replying to")
            print("2. Get replies to those similar tweets")
            print("3. Use those replies as style examples")
        else:
            print("⚠️  TEST INCOMPLETE: Missing data")
            print("\nTo get full functionality:")
            print("1. Run timeline reading with auto_add_to_rag=True")
            print("2. This will populate both ChromaDB and replies table")
            print("3. Then test again")
        print("="*70)

        return success

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
