#!/usr/bin/env python3
"""
Test script for the reply fetching feature.
Validates database schema and basic functionality.
"""

import sys
import os
import sqlite3

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.memory_manager import MemoryManager
from bot.tweet_classifier import TweetClassifier

def test_database_schema():
    """Test that the replies table was created correctly"""
    print("\n=== Testing Database Schema ===")

    mm = MemoryManager()
    conn = sqlite3.connect(mm.db_path)
    cursor = conn.cursor()

    # Check if replies table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='replies'")
    result = cursor.fetchone()

    if result:
        print("✓ Replies table exists")
    else:
        print("✗ Replies table NOT found")
        return False

    # Check table schema
    cursor.execute("PRAGMA table_info(replies)")
    columns = cursor.fetchall()

    expected_columns = ['id', 'parent_tweet_url', 'reply_tweet_id', 'author', 'text', 'url', 'engagement', 'timestamp']
    actual_columns = [col[1] for col in columns]

    print(f"  Columns: {', '.join(actual_columns)}")

    for expected in expected_columns:
        if expected in actual_columns:
            print(f"  ✓ Column '{expected}' exists")
        else:
            print(f"  ✗ Column '{expected}' MISSING")
            return False

    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='replies'")
    indexes = cursor.fetchall()
    index_names = [idx[0] for idx in indexes]

    print(f"  Indexes: {', '.join(index_names)}")

    conn.close()
    return True

def test_memory_manager_methods():
    """Test MemoryManager reply methods"""
    print("\n=== Testing MemoryManager Methods ===")

    mm = MemoryManager()

    # Test log_replies method exists
    if hasattr(mm, 'log_replies'):
        print("✓ log_replies() method exists")
    else:
        print("✗ log_replies() method NOT found")
        return False

    # Test get_replies method exists
    if hasattr(mm, 'get_replies'):
        print("✓ get_replies() method exists")
    else:
        print("✗ get_replies() method NOT found")
        return False

    # Test storing and retrieving replies
    test_parent_url = "https://twitter.com/test/status/123456789"
    test_replies = [
        {
            'id': '111',
            'author': 'user1',
            'text': 'Test reply 1',
            'url': 'https://twitter.com/user1/status/111',
            'engagement': 10
        },
        {
            'id': '222',
            'author': 'user2',
            'text': 'Test reply 2',
            'url': 'https://twitter.com/user2/status/222',
            'engagement': 20
        }
    ]

    print("  Testing log_replies()...")
    mm.log_replies(test_parent_url, test_replies)
    print("  ✓ Replies logged successfully")

    print("  Testing get_replies()...")
    retrieved = mm.get_replies(test_parent_url)

    if len(retrieved) == 2:
        print(f"  ✓ Retrieved {len(retrieved)} replies")
    else:
        print(f"  ✗ Expected 2 replies, got {len(retrieved)}")
        return False

    # Clean up test data
    conn = sqlite3.connect(mm.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM replies WHERE parent_tweet_url = ?", (test_parent_url,))
    conn.commit()
    conn.close()
    print("  ✓ Test data cleaned up")

    return True

def test_tweet_classifier():
    """Test TweetClassifier has reply classification method"""
    print("\n=== Testing TweetClassifier ===")

    try:
        classifier = TweetClassifier()

        # Test classify_replies method exists
        if hasattr(classifier, 'classify_replies'):
            print("✓ classify_replies() method exists")
        else:
            print("✗ classify_replies() method NOT found")
            return False

        # Check if reply_prompt_template file exists (it might not be loaded if API key is missing)
        prompt_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'bot', 'reply_classification_prompt.txt')
        if os.path.exists(prompt_file):
            print("✓ reply_classification_prompt.txt file exists")
        else:
            print("✗ reply_classification_prompt.txt file NOT found")
            return False

        # If classifier is enabled (has API key), check that template is loaded
        if classifier.enabled:
            if hasattr(classifier, 'reply_prompt_template'):
                print("✓ reply_prompt_template loaded (classifier enabled)")
            else:
                print("✗ reply_prompt_template NOT loaded (but classifier is enabled)")
                return False
        else:
            print("  ℹ Classifier disabled (no API key) - prompt template not loaded, but file exists")

        return True

    except Exception as e:
        print(f"✗ Error initializing TweetClassifier: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("Testing Reply Fetching Feature Implementation")
    print("="*50)

    results = []

    # Run tests
    results.append(("Database Schema", test_database_schema()))
    results.append(("MemoryManager Methods", test_memory_manager_methods()))
    results.append(("TweetClassifier", test_tweet_classifier()))

    # Print summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("="*50)

    if all_passed:
        print("\n🎉 All tests passed! The reply fetching feature is ready.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
