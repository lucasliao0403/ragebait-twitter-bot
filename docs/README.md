# Ragebait Twitter Bot

## Overview

An agentic Twitter bot to ragebait tech twitter.

Built using browser-use and tweety-ns.

## Core Functionality

- Tweets are read from timeline using tweety-ns
- Tweets are filtered for quality, then added to /.rag_data for RAG.
- NOT IMPLEMENTED: Timeline is read again, then some tweets are selected to be replied to.
- Logs interactions in /data/memory.db(tweets, replies, timeline reads, etc.)
- TODO: Tracks engagement and personalizes interactions to increase engagement.

**TODO:**
- implement fully autonomous workflow for reply generation
- improve consistency of browser use functions:
    - post tweet doesn't always stop
    - login doesn't always work
- check out cerebras
- clean up (de-slopify) documentation
- clean up logging
- host chromadb somewhere so it doesn't have to initialize every time.
- memory/self improvement: 
    - learns from engagement. currently engagement isn't tracked
