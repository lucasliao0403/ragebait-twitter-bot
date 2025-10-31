#!/usr/bin/env python3
"""
Test script for the tone classification system.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tweety_bot import TweetyBot
import asyncio

# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Thoughtful AI take",
        "tweet": "the hardest part of building AI products isn't the models, it's the context windows and prompt engineering at scale",
        "author": "sama",
        "expected": "supportive"
    },
    {
        "name": "Obvious satire",
        "tweet": "just raised $10M seed to disrupt the $500B pencil industry with AI-powered writing instruments",
        "author": "dril",
        "expected": "funny"
    },
    {
        "name": "Consensus VC wisdom",
        "tweet": "great founders have a reality distortion field and can recruit A+ talent in any market",
        "author": "random_vc",
        "expected": "contrarian"
    },
    {
        "name": "Genuine product insight",
        "tweet": "users don't want more features, they want their problems solved faster",
        "author": "pmarca",
        "expected": "supportive"
    },
    {
        "name": "Hype train",
        "tweet": "AGI in 18 months. scaling laws never break. inevitable.",
        "author": "tech_optimist",
        "expected": "contrarian"
    }
]

async def test_tone_classification():
    """Test tone classification on various tweet types"""
    print("\n" + "="*70)
    print("Testing Dynamic Tone Classification")
    print("="*70)

    # Initialize bot
    print("\n1. Initializing TweetyBot...")
    bot = TweetyBot()

    # We don't need to login for classification testing
    print("   ✓ Bot initialized")

    # Test each case
    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{i}. Test: {test_case['name']}")
        print(f"   Tweet: \"{test_case['tweet']}\"")
        print(f"   Author: @{test_case['author']}")
        print(f"   Expected tone: {test_case['expected']}")

        try:
            # Call tone classifier
            tone_data = bot.classify_tone(
                original_tweet_text=test_case['tweet'],
                original_author=test_case['author'],
                previous_tweets=[],  # Empty for this test
                reply_context=""     # Empty for this test
            )

            classified_tone = tone_data.get('tone')
            reasoning = tone_data.get('reasoning')

            print(f"   ✓ Classified as: {classified_tone}")
            print(f"   Reasoning: {reasoning}")

            # Check if it matches expected
            match = classified_tone == test_case['expected']
            results.append({
                'name': test_case['name'],
                'expected': test_case['expected'],
                'actual': classified_tone,
                'match': match,
                'reasoning': reasoning
            })

            if match:
                print(f"   ✅ Match!")
            else:
                print(f"   ⚠️  Expected {test_case['expected']}, got {classified_tone}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'name': test_case['name'],
                'expected': test_case['expected'],
                'actual': 'ERROR',
                'match': False,
                'reasoning': str(e)
            })

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    matches = sum(1 for r in results if r['match'])
    total = len(results)

    print(f"\nMatches: {matches}/{total}")

    for result in results:
        status = "✅" if result['match'] else "⚠️"
        print(f"{status} {result['name']}: {result['expected']} → {result['actual']}")

    print("\n" + "="*70)

    if matches == total:
        print("🎉 ALL TESTS PASSED!")
    elif matches >= total * 0.6:
        print("✓ MOSTLY WORKING - tone classification is functional")
    else:
        print("⚠️  NEEDS TUNING - many mismatches, consider adjusting prompts")

    print("="*70)

    return matches >= total * 0.6

def main():
    """Run test"""
    try:
        success = asyncio.run(test_tone_classification())
        return success
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
