# Ragebait Twitter Bot

## Overview

An agentic Twitter bot to ragebait tech twitter.

Built using browser-use and tweety-ns.

Current pipeline:
1) Read Timeline
2) Add interesting tweets and their replies to RAG db 
3) Read timeline and select tweets to reply to
4) Replying: 
    1) Fetch relevant tweets from RAG
    2) Determine appropriate tone to reply with
    3) Generate and post reply

## Core Functionality

- Tweets are read from timeline using tweety-ns
- Tweets are filtered for quality, then added to /.rag_data for RAG.
- NOT IMPLEMENTED: Timeline is read again, then some tweets are selected to be replied to.
- Logs interactions in /data/memory.db(tweets, replies, timeline reads, etc.)
- TODO: Tracks engagement and personalizes interactions to increase engagement.
