# CLAUDE.md

claude.ai/code guidance for this repo.

## IMPLEMENTATION RULES

- implement minimum. no extra tests/examples unless asked.
- when editing prompts: minimal changes only. don't touch unrelated text.
- new packages → update requirements.txt
- NEVER read .env files

## Project Overview

twitter bot. uses tweety-ns (reverse-engineered twitter api) for reads, browser-use for writes. learns from interactions via memory + RAG.

**hybrid architecture:**
- tweety_bot.py: fast reads (timeline, search, user tweets)
- browser_bot.py: reliable writes (post, reply)
- test_bot.py: combines both, routes operations to correct bot

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
- openai (embeddings for RAG)
- chromadb (vector db for style examples)
- google-generativeai (gemini for tweet classification)
- python-dotenv

**config/.env:**

# required
TWITTER_SESSION_ID=your_session_id
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
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

### TweetyBot (reads)

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

### BrowserBot (writes)

```python
await bot.start_session()           # browser automation login
await bot.post_tweet("text")
reply = await bot.generate_reply("tweet_url")  # claude 4.5 sonnet
await bot.reply_to_tweet("tweet_url", reply)
await bot.close_session()
```

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
- uses openai embeddings (text-embedding-3-small)
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

**generate_reply(tweet_url):**
1. fetch tweet via tweety-ns
2. get previous tweets from author (memory.db)
3. retrieve similar style tweets (chromadb)
4. combine in prompt with reply_prompt.txt personality
5. call claude 4.5 sonnet (temp=1.0, max_tokens=150)
6. return reply text

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
1. start both sessions
2. post tweet (browser)
3. get timeline (tweety) → auto-adds to RAG
4. get user tweets (tweety)
5. generate + reply (browser + claude)
6. search tweets (tweety)
7. close sessions
```

## Guidelines

- no politics, hate, violence, sexual content
- ragebait style: controversial, hot takes, engagement-optimized
- lowercase casual tech twitter voice

## Future

- host chromadb remotely (avoid local re-init overhead)
