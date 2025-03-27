import pytest
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
    @patch('app.process_book_fetch')
    def test_get_book_endpoint_start(self, mock_process, mock_clean, mock_get_content, mock_get_metadata):
        """Test book fetch initiation"""
        mock_get_metadata.return_value = (self.sample_book_data["metadata"], None)
        mock_get_content.return_value = ("Raw content", None)
        mock_clean.return_value = "Cleaned content"
        mock_process.return_value = None

        with patch('app.book_fetch_tasks', {}) as mock_tasks:
            response = client.post(
                "/api/book",
                json={"book_id": self.test_book_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert "Book fetch started" in data["message"]
            assert data["book_id"] == self.test_book_id

    @patch('app.book_fetch_tasks')
    def test_get_book_endpoint_already_processing(self, mock_book_fetch_tasks):
        """Test book fetch when already in progress"""
        mock_book_fetch_tasks.__contains__.return_value = True
        mock_book_fetch_tasks.__getitem__.return_value = {
            "status": "processing", 
            "progress": 50,
            "message": "Downloading content..."
        }
        
        response = client.post(
            "/api/book",
            json={"book_id": self.test_book_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "in progress" in data["message"].lower()

    @patch('app.book_cache')
    def test_get_book_endpoint_already_cached(self, mock_book_cache):
        """Test book fetch when book is already cached"""
        mock_book_cache.__contains__.return_value = True
        
        response = client.post(
            "/api/book",
            json={"book_id": self.test_book_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert "available" in data["message"].lower()

    @patch.object(gutenberg.GutenbergAPI, 'get_book_metadata')
    def test_get_book_endpoint_error(self, mock_get_metadata):
        """Test book retrieval with error"""
        mock_get_metadata.return_value = ({}, "Book not found")

        with patch('app.book_cache', {}), patch('app.book_fetch_tasks', {}):
            response = client.post(
                "/api/book",
                json={"book_id": "999999999"}
            )

            assert response.status_code == 200
            assert "status" in response.json()
            assert response.json()["status"] == "processing"

    @patch('app.book_cache')
    @patch('app.analysis_tasks')  
    @patch('app.process_book_analysis_incremental')
    def test_analyze_book_endpoint_start(self, mock_process, mock_analysis_tasks, mock_book_cache):
        """Test starting book analysis"""
        mock_book_cache.__contains__.return_value = True
        mock_book_cache.__getitem__.return_value = self.sample_book_data
        mock_analysis_tasks.__contains__.return_value = False
        mock_process.return_value = None
        
        response = client.post(
            "/api/analyze",
            json={"book_id": self.test_book_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "Analysis started" in data["message"]

    @patch('app.book_cache')
    @patch('app.analysis_tasks')
    def test_analyze_book_endpoint_already_processing(self, mock_analysis_tasks, mock_book_cache):
        """Test analyze endpoint when analysis is already in progress"""
        mock_book_cache.__contains__.return_value = True
        mock_analysis_tasks.__contains__.return_value = True
        mock_analysis_tasks.__getitem__.return_value = {
            "status": "processing",
            "progress": 50,
            "message": "Analyzing characters..."
        }
        
        response = client.post(
            "/api/analyze",
            json={"book_id": self.test_book_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "already in progress" in data["message"].lower()

    @patch('app.analysis_cache')
    @patch('app.book_cache')
    def test_analyze_book_endpoint_already_complete(self, mock_book_cache, mock_analysis_cache):
        """Test analyze endpoint when analysis is already complete"""
        mock_book_cache.__contains__.return_value = True
        mock_analysis_cache.__contains__.return_value = True
        
        response = client.post(
            "/api/analyze",
            json={"book_id": self.test_book_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert "complete" in data["message"].lower()

    @patch('app.book_cache')
    @patch('app.book_fetch_tasks')
    def test_analyze_book_endpoint_waiting_for_book(self, mock_book_fetch_tasks, mock_book_cache):
        """Test analyze endpoint when book fetch is still in progress"""
        mock_book_cache.__contains__.return_value = False
        mock_book_fetch_tasks.__contains__.return_value = True
        mock_book_fetch_tasks.__getitem__.return_value = {
            "status": "processing",
            "progress": 50,
            "message": "Downloading content..."
        }
        
        response = client.post(
            "/api/analyze",
            json={"book_id": self.test_book_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "waiting_for_book"
        assert "waiting for book" in data["message"].lower()

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

        assert response.status_code == 422 or response.status_code == 200
        
        response = client.post(
            "/api/book",
            json={"book_id": "a" * 1000}
        )

        assert response.status_code == 422 or response.status_code == 200

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

        assert response.status_code == 422 or response.status_code == 200
        
        if response.status_code == 422:
            assert "detail" in response.json()

    @patch('app.active_tasks')
    def test_active_tasks_endpoint(self, mock_active_tasks):
        """Test the active tasks debug endpoint"""
        mock_active_tasks.__len__.return_value = 2
        mock_active_tasks.__iter__.return_value = iter(["task1", "task2"])
        
        with patch('app.book_fetch_tasks', {"book1": {}}), patch('app.analysis_tasks', {"book1": {}, "book2": {}}):
            response = client.get("/api/active-tasks")
            
            assert response.status_code == 200
            data = response.json()
            assert data["active_task_count"] == 2
            assert len(data["active_tasks"]) == 2
            assert data["book_fetch_tasks"] == 1
            assert data["analysis_tasks"] == 2

    @patch('app.book_cache')
    def test_book_fetch_status_endpoint_complete(self, mock_book_cache):
        """Test book fetch status endpoint with completed fetch"""
        mock_book_cache.__contains__.return_value = True
        
        response = client.get(f"/api/book-fetch-status/{self.test_book_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["progress"] == 100

    @patch('app.book_cache')
    @patch('app.book_fetch_tasks')
    def test_book_fetch_status_endpoint_processing(self, mock_book_fetch_tasks, mock_book_cache):
        """Test book fetch status endpoint with in-progress fetch"""
        mock_book_cache.__contains__.return_value = False
        mock_book_fetch_tasks.__contains__.return_value = True
        mock_book_fetch_tasks.__getitem__.return_value = {
            "status": "processing",
            "progress": 75,
            "message": "Cleaning content..."
        }
        
        response = client.get(f"/api/book-fetch-status/{self.test_book_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 75
        assert "cleaning content" in data["message"].lower()

    @patch('app.book_cache')
    @patch('app.book_fetch_tasks')
    def test_book_fetch_status_endpoint_not_found(self, mock_book_fetch_tasks, mock_book_cache):
        """Test book fetch status endpoint with no fetch found"""
        mock_book_cache.__contains__.return_value = False
        mock_book_fetch_tasks.__contains__.return_value = False
        
        response = client.get(f"/api/book-fetch-status/{self.test_book_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"
        assert "no fetch operation found" in data["message"].lower()

    def test_book_content_endpoint(self):
        """Test getting book content"""
        with patch('app.book_cache', {self.test_book_id: self.sample_book_data}):
            response = client.get(f"/api/book-content/{self.test_book_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert "metadata" in data
            assert "content_preview" in data
            assert "full_content" in data
            assert data["metadata"]["title"] == "Romeo and Juliet"

    def test_book_content_endpoint_not_found(self):
        """Test getting book content that doesn't exist"""
        with patch('app.book_cache', {}), patch('app.book_fetch_tasks', {}):
            response = client.get(f"/api/book-content/99999")
            
            assert response.status_code == 404

    def test_book_content_endpoint_in_progress(self):
        """Test getting book content while fetch is in progress"""
        with patch('app.book_cache', {}), patch('app.book_fetch_tasks', {'99999': {'status': 'processing'}}):
            response = client.get(f"/api/book-content/99999")
            
            assert response.status_code == 202
            assert "still in progress" in response.json()["detail"].lower()
   
    @pytest.mark.asyncio
    async def test_stream_fetch_updates_endpoint(self):
        """Test streaming book fetch updates endpoint"""
        response = client.get(f"/api/fetch-stream/{self.test_book_id}")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_stream_analysis_updates_endpoint(self):
        """Test streaming analysis updates endpoint"""
        response = client.get(f"/api/analysis-stream/{self.test_book_id}")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]