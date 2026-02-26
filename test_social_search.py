#!/usr/bin/env python3
"""
Test script for Twitter and Reddit search tools.
Tests both authentication and fallback modes.
"""

import os
import sys
import asyncio

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'QueryEngine'))

from QueryEngine.tools.twitter_search import TwitterSearchClient, print_twitter_response
from QueryEngine.tools.reddit_search import RedditSearchClient, print_reddit_response


async def test_twitter():
    """Test Twitter search with twikit."""
    print("\n" + "="*80)
    print("TESTING TWITTER SEARCH (twikit)")
    print("="*80)
    
    try:
        client = TwitterSearchClient()
        
        # Test 1: Search for NVIDIA
        print("\n--- Test 1: Search '$NVDA' ---")
        response = await client.search_tweets("$NVDA", max_results=5)
        print_twitter_response(response)
        
        # Test 2: Search by ticker
        print("\n--- Test 2: Search by ticker 'AMD' ---")
        response = await client.search_tweets_by_ticker("AMD", max_results=5)
        print_twitter_response(response)
        
        print("\n✅ Twitter tests completed")
        
    except Exception as e:
        print(f"\n❌ Twitter test failed: {e}")
        import traceback
        traceback.print_exc()


def test_reddit_json_api():
    """Test Reddit search with JSON API fallback (no credentials)."""
    print("\n" + "="*80)
    print("TESTING REDDIT SEARCH (JSON API - No Credentials)")
    print("="*80)
    
    try:
        # Temporarily remove credentials to force JSON API mode
        old_id = os.environ.pop('REDDIT_CLIENT_ID', None)
        old_secret = os.environ.pop('REDDIT_CLIENT_SECRET', None)
        
        client = RedditSearchClient()
        
        # Test 1: Search for NVIDIA
        print("\n--- Test 1: Search 'NVDA earnings' ---")
        response = client.search_posts("NVDA earnings", limit=5)
        print_reddit_response(response)
        
        # Test 2: Get hot posts
        print("\n--- Test 2: Hot posts from r/wallstreetbets ---")
        response = client.get_hot_posts("wallstreetbets", limit=5)
        print_reddit_response(response)
        
        # Test 3: Search by ticker
        print("\n--- Test 3: Search by ticker 'AMD' ---")
        response = client.search_by_ticker("AMD", limit=5)
        print_reddit_response(response)
        
        # Restore credentials
        if old_id:
            os.environ['REDDIT_CLIENT_ID'] = old_id
        if old_secret:
            os.environ['REDDIT_CLIENT_SECRET'] = old_secret
        
        print("\n✅ Reddit JSON API tests completed")
        
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
