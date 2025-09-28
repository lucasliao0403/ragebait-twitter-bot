import asyncio
import json
import time
from datetime import datetime, timedelta
from twikit import Client
from config import Config

class TwitterBot:
    def __init__(self):
        self.config = Config()
        self.client = Client('en-US')
        self.last_request_time = 0
        self.request_count = 0
        self.hour_start = time.time()

    async def authenticate(self):
        """Load cookies or login fresh"""
        try:
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
            self.client.set_cookies(cookies)

            # Test authentication
            await self.client.get_user_by_screen_name(self.config.twitter_username)
            print("Authentication successful using saved cookies")
            return True

        except Exception as e:
            print(f"Authentication failed: {e}")
            print("Run login_twitter.py first to authenticate")
            return False

    def _rate_limit_check(self):
        """Enforce rate limiting"""
        current_time = time.time()

        # Reset hourly counter if needed
        if current_time - self.hour_start > 3600:
            self.request_count = 0
            self.hour_start = current_time

        # Check hourly limit
        if self.request_count >= self.config.max_requests_per_hour:
            raise Exception(f"Hourly rate limit reached ({self.config.max_requests_per_hour} requests)")

        # Enforce minimum delay
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.config.min_delay:
            sleep_time = self.config.min_delay - time_since_last
            print(f"Rate limiting: sleeping {sleep_time:.1f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    async def post_tweet(self, text):
        """Post a tweet with rate limiting"""
        self._rate_limit_check()

        try:
            tweet = await self.client.create_tweet(text=text)
            print(f"Posted tweet: {text[:50]}...")
            return tweet
        except Exception as e:
            print(f"Failed to post tweet: {e}")
            return None

    async def get_timeline(self, count=20):
        """Get home timeline tweets"""
        self._rate_limit_check()

        try:
            tweets = await self.client.get_home_timeline(count=count)
            print(f"Fetched {len(tweets)} tweets from timeline")
            return tweets
        except Exception as e:
            print(f"Failed to get timeline: {e}")
            return []

    async def get_user_tweets(self, username, count=10):
        """Get tweets from a specific user"""
        self._rate_limit_check()

        try:
            user = await self.client.get_user_by_screen_name(username)
            tweets = await self.client.get_user_tweets(user.id, count=count)
            print(f"Fetched {len(tweets)} tweets from @{username}")
            return tweets
        except Exception as e:
            print(f"Failed to get tweets from @{username}: {e}")
            return []

    async def reply_to_tweet(self, tweet_id, text):
        """Reply to a specific tweet"""
        self._rate_limit_check()

        try:
            reply = await self.client.create_tweet(text=text, reply_to=tweet_id)
            print(f"Replied to tweet {tweet_id}: {text[:50]}...")
            return reply
        except Exception as e:
            print(f"Failed to reply to tweet {tweet_id}: {e}")
            return None

    async def search_tweets(self, query, count=10):
        """Search for tweets"""
        self._rate_limit_check()

        try:
            tweets = await self.client.search_tweet(query, count=count)
            print(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
        except Exception as e:
            print(f"Failed to search tweets: {e}")
            return []

    def get_rate_limit_status(self):
        """Get current rate limiting status"""
        current_time = time.time()
        time_until_reset = 3600 - (current_time - self.hour_start)

        return {
            "requests_used": self.request_count,
            "requests_remaining": self.config.max_requests_per_hour - self.request_count,
            "time_until_reset": max(0, time_until_reset)
        }