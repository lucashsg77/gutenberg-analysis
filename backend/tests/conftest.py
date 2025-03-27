import pytest
import os
from unittest.mock import patch, AsyncMock

@pytest.fixture(autouse=True)
def mock_env_variables():
    """Mock environment variables needed for tests"""
    with patch.dict(os.environ, {
        "GROQ_API_KEY": "test-api-key",
    }):
        yield

@pytest.fixture
def sample_book_content():
    """Sample book content for tests"""
    return """
    ROMEO: But, soft! what light through yonder window breaks?
    It is the east, and Juliet is the sun.
    Arise, fair sun, and kill the envious moon,
    Who is already sick and pale with grief,
    That thou her maid art far more fair than she.
    
    JULIET: Romeo, Romeo! wherefore art thou Romeo?
    Deny thy father and refuse thy name;
    Or, if thou wilt not, be but sworn my love,
    And I'll no longer be a Capulet.
    
    MERCUTIO: A plague o' both your houses!
    """

@pytest.fixture
def sample_book_metadata():
    """Sample book metadata for tests"""
    return {
        "id": "1787",
        "title": "Romeo and Juliet",
        "author": "William Shakespeare",
        "language": "English",
        "subject": ["Drama"],
        "release_date": "2021-08-05",
        "downloads": 12345,
        "cover_url": "https://www.gutenberg.org/cache/epub/1787/pg1787.cover.medium.jpg"
    }

@pytest.fixture
def sample_characters_data():
    """Sample character data for tests"""
    return {
        "characters": [
            {
                "name": "Romeo",
                "aliases": ["Romeo Montague"],
                "role": "Main",
                "description": "Young man from Montague family",
                "relationships": [
                    {"character": "Juliet", "type": "Lover", "strength": 10},
                    {"character": "Mercutio", "type": "Friend", "strength": 8}
                ]
            },
            {
                "name": "Juliet",
                "aliases": ["Juliet Capulet"],
                "role": "Main",
                "description": "Young woman from Capulet family",
                "relationships": [
                    {"character": "Romeo", "type": "Lover", "strength": 10},
                    {"character": "Nurse", "type": "Confidant", "strength": 7}
                ]
            },
            {
                "name": "Mercutio",
                "role": "Supporting",
                "description": "Romeo's friend",
                "relationships": [
                    {"character": "Romeo", "type": "Friend", "strength": 8}
                ]
            }
        ]
    }

@pytest.fixture
def sample_analysis_data():
    """Sample analysis results for tests"""
    return {
        "characters": [
            {
                "name": "Romeo",
                "aliases": ["Romeo Montague"],
                "role": "Main",
                "description": "Young man from Montague family",
                "relationships": [
                    {"character": "Juliet", "type": "Lover", "strength": 10}
                ]
            }
        ],
        "graph": {
            "nodes": [{"id": "Romeo", "size": 10, "role": "Main", "description": "Description"}],
            "links": [{"source": "Romeo", "target": "Juliet", "value": 10, "type": "Lover"}]
        },
        "themes": [{"name": "Love", "description": "Description"}],
        "sentiment": {"overall": "mixed", "analysis": "Analysis"},
        "key_quotes": [{"quote": "Quote", "speaker": "Romeo", "context": "Context", "significance": "Significance"}]
    }

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession for async tests"""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="Mock response text")
    
    mock_session.get.return_value.__aenter__.return_value = mock_response
    return mock_session


class MockStreamResponse:
    def __init__(self, chunks):
        self.chunks = chunks
        
    def __iter__(self):
        return iter(self.chunks)

@pytest.fixture
def mock_groq_stream_response():
    """Mock a streaming response from Groq API"""
    from unittest.mock import MagicMock
    import json
    
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock(delta=MagicMock(content='{"partial": "response'))]
    
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock(delta=MagicMock(content=', "more": "data"}'))]
    
    return MockStreamResponse([mock_chunk1, mock_chunk2])