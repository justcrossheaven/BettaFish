#!/usr/bin/env python3
"""
Direct test for Twitter and Reddit search tools.
Imports modules directly without package __init__.
"""

import os
import sys
import asyncio

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env.secrets.local for testing
env_file = os.path.join(os.path.dirname(__file__), '.env.secrets.local')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print(f"✓ Loaded credentials from {env_file}")

# Add paths for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'QueryEngine', 'tools'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'QueryEngine', 'utils'))


async def test_twitter():
    """Test Twitter search with twikit."""
    print("\n" + "="*80)
    print("TESTING TWITTER SEARCH (twikit)")
    print("="*80)
    
    # Direct import
    import twitter_search
    
    try:
        client = twitter_search.TwitterSearchClient()
        
        # Test 1: Search for NVIDIA
        print("\n--- Test 1: Search '$NVDA' ---")
        response = await client.search_tweets("$NVDA", max_results=3)
        
        if response.error:
            print(f"❌ Error: {response.error}")
        else:
            print(f"✅ Found {len(response.results)} tweets in {response.response_time:.2f}s")
            for i, tweet in enumerate(response.results[:3], 1):
                print(f"\n{i}. @{tweet.user_screen_name}:")
                print(f"   {tweet.text[:100]}...")
                print(f"   ♥ {tweet.favorite_count} | RT {tweet.retweet_count}")
        
        print("\n✅ Twitter test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Twitter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reddit_json_api():
    """Test Reddit search with JSON API fallback (no credentials)."""
    print("\n" + "="*80)
    print("TESTING REDDIT SEARCH (JSON API - No Credentials)")
    print("="*80)
    
    # Direct import
    import reddit_search
    
    try:
        # Temporarily remove credentials to force JSON API mode
        old_id = os.environ.pop('REDDIT_CLIENT_ID', None)
        old_secret = os.environ.pop('REDDIT_CLIENT_SECRET', None)
        
        client = reddit_search.RedditSearchClient()
        
        # Test 1: Get hot posts from wallstreetbets
        print("\n--- Test 1: Hot posts from r/wallstreetbets ---")
        response = client.get_hot_posts("wallstreetbets", limit=3)
        
        if response.error:
            print(f"❌ Error: {response.error}")
        else:
            print(f"✅ Found {len(response.posts)} posts in {response.response_time:.2f}s")
            for i, post in enumerate(response.posts[:3], 1):
                tickers = ', '.join(post.mentioned_tickers[:3]) if post.mentioned_tickers else 'None'
                print(f"\n{i}. {post.title[:80]}...")
                print(f"   ↑{post.score} | 💬{post.num_comments} | Tickers: {tickers}")
        
        # Test 2: Search for NVDA
        print("\n--- Test 2: Search 'NVDA' ---")
        response = client.search_posts("NVDA", limit=3)
        
        if response.error:
            print(f"❌ Error: {response.error}")
        else:
            print(f"✅ Found {len(response.posts)} posts in {response.response_time:.2f}s")
            for i, post in enumerate(response.posts[:3], 1):
                print(f"\n{i}. r/{post.subreddit}: {post.title[:60]}...")
                print(f"   ↑{post.score} | 💬{post.num_comments}")
        
        # Restore credentials
        if old_id:
            os.environ['REDDIT_CLIENT_ID'] = old_id
        if old_secret:
            os.environ['REDDIT_CLIENT_SECRET'] = old_secret
        
        print("\n✅ Reddit JSON API test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Reddit test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SOCIAL MEDIA SEARCH INTEGRATION TEST")
    print("="*80)
    
    # Test Reddit (JSON API fallback)
    reddit_ok = test_reddit_json_api()
    
    # Test Twitter (twikit)
    twitter_ok = await test_twitter()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Reddit: {'✅ PASSED' if reddit_ok else '❌ FAILED'}")
    print(f"Twitter: {'✅ PASSED' if twitter_ok else '❌ FAILED'}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
