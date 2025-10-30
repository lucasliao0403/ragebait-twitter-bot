# CLAUDE.md

claude.ai/code guidance for this repo.

## IMPLEMENTATION RULES

- implement minimum. no extra tests/examples unless asked.
- when editing prompts: minimal changes only. don't touch unrelated text.
- when adding or removing packages: ALWAYS update requirements.txt
- NEVER read .env files

## DOCUMENTATION STYLE

write docs direct, concise. sacrifice grammar for brevity.
- "bot fetches tweets" → "fetches tweets"
- "The system uses" → "uses"
- fragments over sentences
- keywords emphasized
- no fluff

## Project Overview

twitter bot. uses tweety-ns (reverse-engineered twitter api) for reads, browser-use for writes. learns from interactions via memory + RAG.

**hybrid architecture (why?):**
- **tweety-ns limitations**: can only READ (timeline, search, user tweets). cannot post or reply.
- **browser-use solution**: handles all WRITES (post tweets, reply to tweets).
- result: tweety for fast reads, browser for necessary writes.

**files:**
- tweety_bot.py: reads only (timeline, search, user tweets)
- browser_bot.py: writes only (post, reply)
- test_bot.py: routes operations to correct bot

## Key References

- [tweety-ns docs](https://mahrtayyab.github.io/tweety_docs/): twitter api lib
- [tweety-ns github](https://github.com/mahrtayyab/tweety): source + examples

## Setup

```bash
pip install -r requirements.txt
```

**requirements.txt:**
- tweety-ns (twitter api)
- browser-use (posting/replies)
- anthropic (claude for replies)
- chromadb (vector db for style examples)
- google-generativeai (gemini for embeddings + tweet classification)
- python-dotenv

**config/.env:**

# required
TWITTER_SESSION_ID=your_session_id
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...        # embeddings + classification
GROQ_API_KEY=...

# optional (browser-use fallback)
TWITTER_USERNAME=...
TWITTER_PASSWORD=...


## File Structure

src/bot/
  tweety_bot.py       # reads: get timeline, search tweets, get user tweets
  browser_bot.py      # writes: post tweet, reply to tweet
  memory_manager.py   # sqlite memory (interactions, friends, conversations)
  style_rag.py        # chromadb for RAG
  tweet_classifier.py # selects tweets to add to RAG using gemini
  reply_prompt.txt    # bot personality prompt

scripts/
  test_bot.py         # CLI for manual testing
  import_tweets.py    # add tweets to RAG from tweets.txt
  tweets.txt          # tweet URLs for style training

data/
  memory.db           # sqlite: interactions, friends, conversations

.rag_data/
  chroma.sqlite3      # chromadb: style example tweets

## Core Functionality

### TweetyBot (reads only - tweety-ns can't write)

```python
await bot.start_session()           # auth with TWITTER_SESSION_ID
tweets = await bot.get_timeline(500) # auto-filters to RAG via gemini
tweets = await bot.get_user_tweets("username", 20)
tweets = await bot.search_tweets("query", 50)
await bot.close_session()
```

**auto-filter:** get_timeline() automatically:
1. fetches tweets using cursor pagination
2. classifies via gemini 2.5 flash lite (40 tweets/batch)
3. adds high-quality tweets to RAG
4. logs all to memory.db

**why use tweety?** 10-100x faster than browser automation. structured data. no UI parsing.

### BrowserBot (writes only - tweety-ns can't post/reply)

```python
await bot.start_session()           # browser automation login
await bot.post_tweet("text")
reply = await bot.generate_reply("tweet_url")  # claude 4.5 sonnet
await bot.reply_to_tweet("tweet_url", reply)
await bot.close_session()
```

**why use browser?** tweety-ns cannot post or reply. only option for writes.

## Memory System (SQLite)

**data/memory.db tables:**

- `interactions`: all tweet reads/writes
  - type, author, content, url, timestamp, metadata
  - indexes: timestamp, author, type

- `friends`: interaction tracking per user
  - username, last_interaction, interaction_count

- `conversations`: thread tracking
  - thread_id, tweets (json), participants (json), last_updated

**usage:**
```python
memory = MemoryManager()
memory.log_interaction({...})
memory.update_friend_profile(username)
memory.log_conversation(thread_id, original_tweet, reply_tweet)
```

## RAG System (ChromaDB)

**style_rag.py:**
- learns writing style from example tweets
- stores in .rag_data/chroma.sqlite3
- uses gemini embeddings (gemini-embedding-001, 768-dim, normalized)
- task types: RETRIEVAL_DOCUMENT (storing), RETRIEVAL_QUERY (searching)
- retrieves similar tweets for reply generation context

**adding tweets:**
```python
# manual: scripts/import_tweets.py
# auto: get_timeline(auto_add_to_rag=True)  # default
```

**tweet_classifier.py:**
- gemini 2.5 flash lite scores tweets
- accepts: strong voice, concise, hot takes, tech culture, engagement-bait
- rejects: spam, news links, announcements, threads (1/n), too long

## AI Reply Generation

**correct pattern:**
```python
# 1. tweety reads + generates reply (fast, reliable)
reply = await tweety_bot.generate_reply(tweet_url)

# 2. browser posts reply (only writes)
await browser_bot.reply_to_tweet(tweet_url, reply)
```

**tweety_bot.generate_reply(tweet_url):**
1. fetch tweet via tweety-ns (read operation - uses tweet_detail())
2. get previous tweets from author (memory.db)
3. retrieve similar style tweets (chromadb)
4. combine in prompt with reply_prompt.txt personality
5. call claude 4.5 sonnet (temp=1.0, max_tokens=150)
6. return reply text (does NOT post)

**browser_bot.reply_to_tweet(tweet_url, text):**
- clicks reply button
- types text
- submits

**why split?**
- browser_bot.generate_reply() loops forever trying to extract tweet data (browser-use unreliable at data extraction)
- tweety-ns reliable for reads, browser-use only for writes

## Session Management

**tweety-ns (reads):**
- uses TWITTER_SESSION_ID from .env
- saves to twitter_session.tw_session file (gitignored)
- no re-auth needed between runs

**browser-use (writes):**
- browser automation
- saved profile in .browser_profile/ (gitignored)

## Rate Limits

- tweety-ns: handles twitter rate limits internally
- add 2-3s delays between batch ops
- cursor pagination: fetch exactly N tweets, no over-fetching
- "abusing tweety can lead to read_only account" - use conservatively

## Testing

```bash
python scripts/test_bot.py

# options:
1. start both sessions (tweety + browser)
2. post tweet (browser)
3. get timeline (tweety) → auto-adds to RAG
4. get user tweets (tweety)
5. generate + reply (tweety reads/generates, browser posts)
6. search tweets (tweety)
7. close sessions
8. exit
```

## Guidelines

- no politics, hate, violence, sexual content
- ragebait style: controversial, hot takes, engagement-optimized
- lowercase casual tech twitter voice

**TODO:**
Most important:

- improve timeline reading - for each tweet,
  - fetch top 5 highest engagement replies from tweets and store those with the original tweet
- implement fully autonomous workflow for reply generation
  - create run_bot.py with learning loop and replying loop
- clean up logging
- host chromadb somewhere so it doesn't have to initialize every time.
- memory/self improvement: 
    - learns from engagement. currently engagement isn't tracked
- improve consistency of browser use functions:
    - post tweet doesn't always stop
    - login doesn't always work
- check out cerebras to replace groq
- dynamic number of RAG results (currently hardcoded to 12 in tweety_bot.py)
