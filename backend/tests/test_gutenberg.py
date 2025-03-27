from unittest.mock import patch
import responses
import requests
from bs4 import BeautifulSoup

from gutenberg import GutenbergAPI

class TestGutenbergAPI:
    """Tests for the GutenbergAPI class"""

    def setup_method(self):
        """Set up before each test"""
        self.api = GutenbergAPI()
        self.test_book_id = "1787"

    @responses.activate
    def test_get_book_content_success(self):
        """Test successful book content retrieval"""
        test_content = "This is the book content"
        responses.add(
            responses.GET,
            f"{self.api.base_url}/files/{self.test_book_id}/{self.test_book_id}-0.txt",
            body=test_content,
            status=200
        )

        content, error = self.api.get_book_content(self.test_book_id)

        assert error is None
        assert content == test_content
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_book_content_fallback_formats(self):
        """Test fallback to alternative formats when primary format fails"""
        responses.add(
            responses.GET,
            f"{self.api.base_url}/files/{self.test_book_id}/{self.test_book_id}-0.txt",
            status=404
        )

        test_content = "This is the book content from secondary format"
        responses.add(
            responses.GET,
            f"{self.api.base_url}/cache/epub/{self.test_book_id}/pg{self.test_book_id}.txt",
            body=test_content,
            status=200
        )

        content, error = self.api.get_book_content(self.test_book_id)

        assert error is None
        assert content == test_content
        assert len(responses.calls) == 2

    @responses.activate
    def test_get_book_content_all_formats_fail(self):
        """Test handling when all content formats fail"""
        responses.add(
            responses.GET,
            f"{self.api.base_url}/files/{self.test_book_id}/{self.test_book_id}-0.txt",
            status=404
        )
        responses.add(
            responses.GET,
            f"{self.api.base_url}/cache/epub/{self.test_book_id}/pg{self.test_book_id}.txt",
            status=404
        )
        responses.add(
            responses.GET,
            f"{self.api.base_url}/ebooks/{self.test_book_id}.txt.utf-8",
            status=404
        )

        content, error = self.api.get_book_content(self.test_book_id)

        assert error is not None
        assert "Failed to fetch book content" in error
        assert content == ""
        assert len(responses.calls) == 3

    @responses.activate
    def test_get_book_metadata_success(self):
        """Test successful book metadata retrieval"""
        html_content = """
        <html>
            <head><title>Romeo and Juliet</title></head>
            <body>
                <h1 itemprop="name">Romeo and Juliet</h1>
                <a itemprop="creator">William Shakespeare</a>
                <tr><td>Language</td><td>English</td></tr>
                <td property="dcterms:subject"><a>Drama</a></td>
                <td itemprop="datePublished">2021-08-05</td>
                <td itemprop="interactionCount">12345 downloads</td>
            </body>
        </html>
        """
        responses.add(
            responses.GET,
            f"{self.api.base_url}/ebooks/{self.test_book_id}",
            body=html_content,
            status=200
        )

        metadata, error = self.api.get_book_metadata(self.test_book_id)

        assert error is None
        assert metadata['id'] == self.test_book_id
        assert metadata['title'] == "Romeo and Juliet"
        assert metadata['author'] == "William Shakespeare"
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_book_metadata_failure(self):
        """Test handling of metadata retrieval failure"""
        responses.add(
            responses.GET,
            f"{self.api.base_url}/ebooks/{self.test_book_id}",
            status=404
        )

        metadata, error = self.api.get_book_metadata(self.test_book_id)

        assert error is not None
        assert "Failed to fetch book metadata" in error
        assert metadata == {}
        assert len(responses.calls) == 1

    def test_clean_book_content(self):
        """Test cleaning of book content"""
        raw_content = """
        Project Gutenberg's Romeo and Juliet, by William Shakespeare
        This eBook is for the use of anyone anywhere
        
        *** START OF THIS PROJECT GUTENBERG EBOOK ROMEO AND JULIET ***
        
        THE ACTUAL BOOK CONTENT GOES HERE
        ROMEO: But, soft! what light through yonder window breaks?
        JULIET: Romeo, Romeo! wherefore art thou Romeo?
        
        *** END OF THIS PROJECT GUTENBERG EBOOK ROMEO AND JULIET ***
        
        This and all associated files are distributed in the hopes...
        """

        cleaned_content = self.api.clean_book_content(raw_content)

        assert "THE ACTUAL BOOK CONTENT GOES HERE" in cleaned_content
        assert "ROMEO: But, soft!" in cleaned_content
        assert "Project Gutenberg's Romeo and Juliet" not in cleaned_content
        assert "*** END OF THIS PROJECT GUTENBERG EBOOK" not in cleaned_content
        assert "This and all associated files" not in cleaned_content

    def test_extract_cover_url(self):
        """Test extraction of cover URL"""
        html = """
        <html>
            <body>
                <img src="/cache/epub/1787/pg1787.cover.medium.jpg" alt="Cover">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        cover_url = self.api._extract_cover_url(soup, self.test_book_id)

        assert "www.gutenberg.org/cache/epub/1787/pg1787.cover.medium.jpg" in cover_url

    @patch('requests.get')
    def test_exception_handling(self, mock_get):
        """Test exception handling in API methods"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection error")

        content, error = self.api.get_book_content(self.test_book_id)
        assert error is not None
        assert "Error:" in error
        assert content == ""
        
        metadata, error = self.api.get_book_metadata(self.test_book_id)
        assert error is not None
        assert "Error:" in error
        assert metadata == {}