"""
Mock PRAW (Reddit) module for testing Reddit client functionality.
"""

from unittest.mock import Mock, MagicMock


class MockPRAW:
    """Mock implementation of PRAW for testing."""
    
    @staticmethod
    def create_submission(post_id="abc123", title="Test Post", score=100):
        """Create a mock Reddit submission."""
        submission = Mock()
        submission.id = post_id
        submission.title = title
        submission.selftext = f"This is the body of {title}"
        submission.score = score
        submission.upvote_ratio = 0.85
        submission.num_comments = 42
        submission.created_utc = 1706637600
        submission.url = f"https://reddit.com/r/test/{post_id}"
        submission.permalink = f"/r/test/comments/{post_id}"
        submission.is_self = True
        submission.link_flair_text = "Discussion"
        submission.total_awards_received = 5
        
        # Mock subreddit
        submission.subreddit = Mock()
        submission.subreddit.__str__ = lambda x: "wallstreetbets"
        
        # Mock author
        submission.author = Mock()
        submission.author.__str__ = lambda x: "test_user"
        
        return submission
    
    @staticmethod
    def create_comment(comment_id="xyz789", body="Great post!", score=25):
        """Create a mock Reddit comment."""
        comment = Mock()
        comment.id = comment_id
        comment.body = body
        comment.score = score
        comment.created_utc = 1706638800
        comment.parent_id = "t3_abc123"
        comment.is_submitter = False
        
        # Mock author
        comment.author = Mock()
        comment.author.__str__ = lambda x: "commenter"
        
        return comment
    
    @staticmethod
    def create_reddit_client():
        """Create a mock Reddit client."""
        reddit = Mock()
        
        # Mock subreddit method
        def mock_subreddit(name):
            sub = Mock()
            
            # Mock search
            sub.search = Mock(return_value=[
                MockPRAW.create_submission("post1", "$NVDA to the moon", 500),
                MockPRAW.create_submission("post2", "AMD earnings discussion", 300)
            ])
            
            # Mock hot
            sub.hot = Mock(return_value=[
                MockPRAW.create_submission("hot1", "Market Discussion", 1000),
                MockPRAW.create_submission("hot2", "Daily Thread", 750)
            ])
            
            # Mock new
            sub.new = Mock(return_value=[
                MockPRAW.create_submission("new1", "Breaking News", 50),
                MockPRAW.create_submission("new2", "Just Posted", 10)
            ])
            
            return sub
        
        reddit.subreddit = mock_subreddit
        
        # Mock submission method
        def mock_submission(id):
            sub = MockPRAW.create_submission(post_id=id)
            sub.comments = Mock()
            sub.comments.replace_more = Mock()
            sub.comments.list = Mock(return_value=[
                MockPRAW.create_comment("c1", "First comment", 100),
                MockPRAW.create_comment("c2", "Second comment", 50),
                MockPRAW.create_comment("c3", "Third comment", 25)
            ])
            return sub
        
        reddit.submission = mock_submission
        
        return reddit
