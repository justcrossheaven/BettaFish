#!/usr/bin/env python3
"""
Simple direct test for Twitter and Reddit search tools.
Avoids loading full agent dependencies.
"""

import os
import sys
import asyncio

# Direct imports to avoid loading the full agent
sys.path.insert(0, os.path.dirname(__file__))

# Set up minimal environment
os.chdir(os.path.dirname(__file__))


async def test_twitter():
    """Test Twitter search with twikit."""
    print("\n" + "="*80)
    print("TESTING TWITTER SEARCH (twikit)")
    print("="*80)
    
    # Import here to isolate from other dependencies
    from QueryEngine.tools import twitter_search
    
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
        
    except Exception as e:
        print(f"\n❌ Twitter test failed: {e}")
        import traceback
        traceback.print_exc()


def test_reddit_json_api():
    """Test Reddit search with JSON API fallback (no credentials)."""
    print("\n" + "="*80)
    print("TESTING REDDIT SEARCH (JSON API - No Credentials)")
    print("="*80)
    
    # Import here to isolate from other dependencies
    from QueryEngine.tools import reddit_search
    
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
                print(f"   {post.permalink}")
        
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
        
    except Exception as e:
        print(f"\n❌ Reddit test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SOCIAL MEDIA SEARCH INTEGRATION TEST")
    print("="*80)
    
    # Test Reddit (JSON API fallback)
    test_reddit_json_api()
    
    # Test Twitter (twikit)
    await test_twitter()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
