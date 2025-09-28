import asyncio
import json
import time
from twikit import Client
from config import Config

async def login_and_save_cookies():
    config = Config()

    # Use random user agent to avoid detection
    client = Client(language='en-US')

    try:
        # Try to load existing cookies first
        try:
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
            client.set_cookies(cookies)
            print("Loaded existing cookies from cookies.json")

            # Test if cookies are still valid with delay
            time.sleep(2)
            await client.get_user_by_screen_name(config.twitter_username)
            print("Cookies are still valid!")
            return client

        except (FileNotFoundError, Exception) as e:
            print(f"No valid cookies found: {e}")
            print("Attempting fresh login...")

        # Add delay before login attempt
        time.sleep(5)

        # Fresh login with retry logic
        print(f"Logging in as {config.twitter_username}...")
        try:
            await client.login(
                auth_info_1=config.twitter_username,
                auth_info_2=config.twitter_email,
                password=config.twitter_password
            )
        except Exception as login_error:
            if "403" in str(login_error) or "Cloudflare" in str(login_error):
                print("ERROR: Blocked by Cloudflare/Twitter bot detection")
                return None
            else:
                raise login_error

        # Save cookies
        cookies = client.get_cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)

        print("Login successful! Cookies saved to cookies.json")
        return client

    except Exception as e:
        print(f"Login failed: {e}")
        return None

if __name__ == "__main__":
    client = asyncio.run(login_and_save_cookies())
    if client:
        print("Ready to use Twitter bot!")
    else:
        print("Failed to authenticate with Twitter")