from fastapi.testclient import TestClient
from unittest.mock import patch

from app import app
import gutenberg

client = TestClient(app)

class TestAPI:
    """Integration tests for the FastAPI endpoints"""

    def setup_method(self):
        """Setup before each test"""
        self.test_book_id = "1787"
        self.sample_book_data = {
            "metadata": {
                "id": self.test_book_id,
                "title": "Romeo and Juliet",
                "author": "William Shakespeare",
                "language": "English",
                "subject": ["Drama"],
                "release_date": "2021-08-05",
                "downloads": 12345,
                "cover_url": "https://www.gutenberg.org/cache/epub/1787/pg1787.cover.medium.jpg"
            },
            "content_preview": "This is a preview of the content...",
            "content_length": 100000,
            "full_content": "This is the full content of the book..."
        }
        
        self.sample_analysis_data = {
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

    def test_root_endpoint(self):
        """Test the root endpoint returns a message"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "running" in response.json()["message"]

    @patch.object(gutenberg.GutenbergAPI, 'get_book_metadata')
    @patch.object(gutenberg.GutenbergAPI, 'get_book_content')
    @patch.object(gutenberg.GutenbergAPI, 'clean_book_content')
    def test_get_book_endpoint_success(self, mock_clean, mock_get_content, mock_get_metadata):
        """Test successful book retrieval"""
        mock_get_metadata.return_value = (self.sample_book_data["metadata"], None)
        mock_get_content.return_value = ("Raw content", None)
        mock_clean.return_value = "Cleaned content"

        response = client.post(
            "/api/book",
            json={"book_id": self.test_book_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["title"] == "Romeo and Juliet"
        assert data["metadata"]["author"] == "William Shakespeare"
        assert "content_preview" in data
        assert "content_length" in data
        assert "full_content" not in data

    @patch.object(gutenberg.GutenbergAPI, 'get_book_metadata')
    def test_get_book_endpoint_error(self, mock_get_metadata):
        """Test book retrieval with error"""
        mock_get_metadata.return_value = ({}, "Book not found")

        response = client.post(
            "/api/book",
            json={"book_id": "999999999"}
        )

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Book not found" in response.json()["detail"]

    @patch('app.book_cache')
    @patch('app.analysis_tasks')  
    @patch('fastapi.BackgroundTasks.add_task')
    def test_analyze_book_endpoint_start(self, mock_add_task, mock_analysis_tasks, mock_book_cache):
        mock_book_cache.__getitem__.return_value = self.sample_book_data
        mock_analysis_tasks.__contains__.return_value = False
        
        response = client.post(
            "/api/analyze",
            json={"book_id": self.test_book_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "Analysis started" in data["message"]
        mock_add_task.assert_called_once()

    @patch('app.analysis_tasks')
    def test_analysis_status_endpoint(self, mock_analysis_tasks):
        """Test checking analysis status"""
        mock_analysis_tasks.__contains__.return_value = True
        mock_analysis_tasks.__getitem__.return_value = {
            "status": "processing", 
            "progress": 50, 
            "message": "Analyzing characters"
        }

        response = client.get(f"/api/analysis-status/{self.test_book_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["message"] == "Analyzing characters"

    @patch('app.analysis_cache')
    @patch('app.analysis_tasks')
    def test_get_analysis_results_complete(self, mock_analysis_tasks, mock_analysis_cache):
        """Test getting completed analysis results"""
        mock_analysis_cache.__contains__.return_value = True
        mock_analysis_cache.__getitem__.return_value = self.sample_analysis_data

        response = client.get(f"/api/analysis/{self.test_book_id}")

        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert "graph" in data
        assert "themes" in data
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "Romeo"

    @patch('app.analysis_cache')
    @patch('app.analysis_tasks')
    def test_get_analysis_results_in_progress(self, mock_analysis_tasks, mock_analysis_cache):
        """Test getting analysis results while still processing"""
        mock_analysis_cache.__contains__.return_value = False
        mock_analysis_tasks.__contains__.return_value = True
        mock_analysis_tasks.__getitem__.return_value = {"status": "processing"}
        
        response = client.get(f"/api/analysis/{self.test_book_id}")

        assert response.status_code == 202
        assert "detail" in response.json()
        assert "in progress" in response.json()["detail"]

    @patch('app.analysis_cache')
    @patch('app.analysis_tasks')
    def test_get_analysis_results_not_found(self, mock_analysis_tasks, mock_analysis_cache):
        """Test getting analysis results that don't exist"""
        mock_analysis_cache.__contains__.return_value = False
        mock_analysis_tasks.__contains__.return_value = False

        response = client.get(f"/api/analysis/{self.test_book_id}")

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_book_id_format(self):
        """Test handling of invalid book ID format"""
        response = client.post(
            "/api/book",
            json={"book_id": ""}
        )

        assert response.status_code == 404 or response.status_code == 400

        response = client.post(
            "/api/book",
            json={"book_id": "a" * 1000}
        )

        assert response.status_code == 404 or response.status_code == 422

    def test_request_validation(self):
        """Test request validation"""
        response = client.post(
            "/api/book",
            json={}
        )

        assert response.status_code == 422
        assert "detail" in response.json()

        response = client.post(
            "/api/book",
            json={"book_id": 1787}
        )

        assert response.status_code in [200, 422]
        
        if response.status_code == 422:
            assert "detail" in response.json()