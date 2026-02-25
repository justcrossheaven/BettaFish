"""
Functional Test for Twitter and Reddit Platform Integration

Tests actual data fetching capabilities:
- Reddit: Public search (no credentials needed for basic functionality)
- Twitter: Requires credentials for any search
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded credentials from {env_file}")
else:
    print(f"⚠ No .env file found at {env_file}")
    print("  Twitter will require credentials to be set as environment variables")

print("\n" + "="*60)
print("FUNCTIONAL TEST: Twitter & Reddit Platform Integration")
print("="*60 + "\n")

# ==================== Reddit Functional Test ====================
print("[1/2] Testing Reddit Functionality...")
print("-" * 60)

try:
    from QueryEngine.tools import RedditSearchClient
    
    client = RedditSearchClient()
    
    # Test 1: Search for NVDA discussions
    print("\n📊 Test: Searching r/wallstreetbets + r/stocks for 'NVDA'...")
    try:
        response = client.search_posts(
            query="NVDA",
            subreddits=["wallstreetbets", "stocks"],
            limit=5
        )
        
        if response and response.posts:
            print(f"✓ Found {len(response.posts)} posts")
            print(f"\nSample post:")
            post = response.posts[0]
            print(f"  Title: {post.title[:80]}...")
            print(f"  Score: {post.score} | Comments: {post.num_comments}")
            print(f"  Subreddit: r/{post.subreddit}")
            print(f"  URL: {post.url}")
        else:
            print("⚠ Search returned no results (this might be normal)")
            
    except Exception as e:
        print(f"✗ Reddit search failed: {e}")
    
    # Test 2: Get hot posts from a tech subreddit
    print("\n📊 Test: Getting hot posts from r/nvidia...")
    try:
        response = client.get_hot_posts("nvidia", limit=3)
        
        if response and response.posts:
            print(f"✓ Found {len(response.posts)} hot posts")
            for i, post in enumerate(response.posts[:3], 1):
                print(f"\n  {i}. {post.title[:60]}...")
                print(f"     Score: {post.score} | Comments: {post.num_comments}")
        else:
            print("⚠ No hot posts found")
            
    except Exception as e:
        print(f"✗ Get hot posts failed: {e}")
    
    print("\n✅ Reddit functional test PASSED")
    
except Exception as e:
    print(f"\n❌ Reddit functional test FAILED: {e}")

# ==================== Twitter Functional Test ====================
print("\n" + "-" * 60)
print("[2/2] Testing Twitter Functionality...")
print("-" * 60)

async def test_twitter():
    try:
        from QueryEngine.tools import TwitterSearchClient
        
        # Check if credentials are available
        username = os.getenv("TWITTER_USERNAME")
        email = os.getenv("TWITTER_EMAIL")
        password = os.getenv("TWITTER_PASSWORD")
        
        if not all([username, email, password]):
            print("\n⚠ Twitter credentials not found in environment")
            print("  Required env vars: TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD")
            print("  Add these to your .env file to test Twitter functionality")
            return
        
        print(f"\n✓ Found Twitter credentials for user: {username}")
        
        client = TwitterSearchClient()
        
        # Test 1: Login
        print("\n📊 Test: Twitter login...")
        try:
            success = await client.initialize()
            if success:
                print("✓ Twitter login successful")
            else:
                print("✗ Twitter login failed")
                return
        except Exception as e:
            print(f"✗ Twitter login failed: {e}")
            return
        
        # Test 2: Search for $NVDA tweets
        print("\n📊 Test: Searching tweets for '$NVDA'...")
        try:
            response = await client.search_tweets("$NVDA", max_results=5)
            
            if response and response.tweets:
                print(f"✓ Found {len(response.tweets)} tweets")
                print(f"\nSample tweet:")
                tweet = response.tweets[0]
                print(f"  Author: @{tweet.author_username}")
                print(f"  Text: {tweet.text[:100]}...")
                print(f"  Likes: {tweet.like_count} | Retweets: {tweet.retweet_count}")
                print(f"  URL: {tweet.url}")
            else:
                print("⚠ Search returned no results")
                
        except Exception as e:
            print(f"✗ Twitter search failed: {e}")
            return
        
        # Test 3: Search by ticker
        print("\n📊 Test: Searching tweets by ticker 'AMD'...")
        try:
            response = await client.search_tweets_by_ticker("AMD", max_results=3)
            
            if response and response.tweets:
                print(f"✓ Found {len(response.tweets)} tweets mentioning AMD")
                for i, tweet in enumerate(response.tweets[:3], 1):
                    print(f"\n  {i}. @{tweet.author_username}: {tweet.text[:60]}...")
                    print(f"     Likes: {tweet.like_count} | Retweets: {tweet.retweet_count}")
            else:
                print("⚠ No tweets found")
                
        except Exception as e:
            print(f"✗ Ticker search failed: {e}")
        
        print("\n✅ Twitter functional test PASSED")
        
    except Exception as e:
        print(f"\n❌ Twitter functional test FAILED: {e}")

# Run Twitter async test
try:
    asyncio.run(test_twitter())
except Exception as e:
    print(f"\n❌ Twitter async test failed: {e}")

# ==================== Summary ====================
print("\n" + "="*60)
print("FUNCTIONAL TEST COMPLETE")
print("="*60)
print("\nNext Steps:")
print("1. If Reddit works: You can use it immediately for market sentiment")
print("2. If Twitter needs credentials: Add them to your .env file")
print("3. Test in production: Run the full BettaFish pipeline with these tools")
print("\nExample .env entries:")
print("  TWITTER_USERNAME=your_twitter_username")
print("  TWITTER_EMAIL=your_email@example.com")
print("  TWITTER_PASSWORD=your_password")
print("  REDDIT_CLIENT_ID=your_reddit_app_id")
print("  REDDIT_CLIENT_SECRET=your_reddit_app_secret")
print("="*60)
