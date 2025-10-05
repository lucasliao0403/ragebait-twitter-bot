# Scripts

Utility scripts for managing the Twitter bot.

## import_tweets.py

Import style tweets from Twitter URLs into the RAG database.

### Setup

```bash
# Install Selenium
pip install selenium

# Install ChromeDriver
# macOS
brew install chromedriver

# Linux
sudo apt-get install chromium-chromedriver

# Windows
# Download from: https://chromedriver.chromium.org/
```

### Usage

1. **Edit the script** and add your tweet URLs:

```python
TWEET_URLS = [
    "https://twitter.com/sama/status/1234567890123456789",
    "https://twitter.com/karpathy/status/9876543210987654321",
    # Add more...
]
```

2. **Run the script:**

```bash
python scripts/import_tweets.py
```

3. **Watch it scrape and import:**

```
📋 Found 10 tweet URLs to import
🌐 Starting Chrome WebDriver...
✅ WebDriver ready

[1/10] Processing: https://twitter.com/sama/status/...
  ✅ Scraped: @sama: "the right amount of crazy is a lot"
  💾 Added to RAG database

[2/10] Processing: https://twitter.com/karpathy/status/...
  ✅ Scraped: @karpathy: "llms are calculators for words"
  💾 Added to RAG database

...

✅ Successfully imported: 8
❌ Failed: 2
📊 Total tweets in database: 32
```

### Optional: Categorize Tweets

```python
TWEET_CATEGORIES = {
    "https://twitter.com/sama/status/123...": "advice",
    "https://twitter.com/karpathy/status/456...": "observation",
}
```

### Troubleshooting

**"Failed to start WebDriver"**
- Make sure ChromeDriver is installed and in PATH
- Try: `which chromedriver` (should show path)

**"Timeout waiting for tweet to load"**
- Twitter may be rate limiting
- Try running with `headless=False` to see browser
- Add longer delays between requests

**"Could not extract tweet text"**
- Twitter's HTML structure may have changed
- Check if tweet URL is valid
- Try opening URL in browser to verify it loads

### Tips

- Start with 10-20 tweets to test
- Use tweets with high engagement (100+ likes)
- Focus on brief, punchy tweets (3-8 words ideal)
- Mix different authors for diverse style
