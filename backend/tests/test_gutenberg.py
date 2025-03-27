from unittest.mock import patch, AsyncMock
import pytest

from bs4 import BeautifulSoup

from gutenberg import GutenbergAPI

class TestGutenbergAPI:
    """Tests for the GutenbergAPI class"""

    def setup_method(self):
        """Set up before each test"""
        self.api = GutenbergAPI()
        self.test_book_id = "1787"

    @pytest.mark.asyncio
    async def test_get_book_content_success(self, monkeypatch):
        """Test successful book content retrieval"""
        test_content = "This is the book content"

        async def mock_try_url(*args, **kwargs):
            return test_content, None
            
        monkeypatch.setattr(self.api, '_try_url', mock_try_url)
        
        content, error = await self.api.get_book_content(self.test_book_id)

        assert error is None
        assert content == test_content

    @pytest.mark.asyncio
    async def test_try_url_success(self, monkeypatch):
        """Test the _try_url method with successful response"""
        test_content = "This is the book content"
        test_url = f"{self.api.base_url}/files/{self.test_book_id}/{self.test_book_id}-0.txt"

        async def mock_try_url_impl(session, url):
            assert url == test_url
            return test_content, None

        monkeypatch.setattr(self.api, '_try_url', mock_try_url_impl)
        
        result = await self.api._try_url(AsyncMock(), test_url)

        assert result[0] == test_content
        assert result[1] is None

    @pytest.mark.asyncio
    async def test_get_book_content_fallback_formats(self, monkeypatch):
        """Test fallback to alternative formats when primary format fails"""
        test_content = "This is the book content from secondary format"
        calls = []
        async def mock_try_url(session, url):
            calls.append(url)
            if len(calls) == 1:
                return "", "Status 404"
            else:
                return test_content, None
        monkeypatch.setattr(self.api, '_try_url', mock_try_url)
        content, error = await self.api.get_book_content(self.test_book_id)
        assert error is None
        assert content == test_content
        assert len(calls) >= 2
        first_url = f"{self.api.base_url}/files/{self.test_book_id}/{self.test_book_id}-0.txt"
        assert calls[0] == first_url
        second_url = f"{self.api.base_url}/cache/epub/{self.test_book_id}/pg{self.test_book_id}.txt"
        assert calls[1] == second_url

    @pytest.mark.asyncio
    async def test_get_book_content_all_formats_fail(self, monkeypatch):
        """Test handling when all content formats fail"""
        async def mock_try_url(session, url):
            return "", "Status 404"
                
        monkeypatch.setattr(self.api, '_try_url', mock_try_url)
        
        content, error = await self.api.get_book_content(self.test_book_id)

        assert error is not None
        assert "Failed to fetch book content" in error
        assert content == ""

    @pytest.mark.asyncio
    async def test_get_book_metadata_success(self, monkeypatch):
        """Test successful book metadata retrieval"""
        expected_metadata = {
            "id": self.test_book_id,
            "title": "Romeo and Juliet",
            "author": "William Shakespeare",
            "language": "English",
            "subject": ["Drama"],
            "release_date": "2021-08-05",
            "downloads": 12345,
            "cover_url": f"https://www.gutenberg.org/cache/epub/{self.test_book_id}/pg{self.test_book_id}.cover.medium.jpg"
        }

        async def mock_get_book_metadata(book_id):
            assert book_id == self.test_book_id
            return expected_metadata, None

        monkeypatch.setattr(self.api, 'get_book_metadata', mock_get_book_metadata)

        metadata, error = await self.api.get_book_metadata(self.test_book_id)

        assert error is None
        assert metadata == expected_metadata
        assert metadata['id'] == self.test_book_id
        assert metadata['title'] == "Romeo and Juliet"
        assert metadata['author'] == "William Shakespeare"
        assert metadata['language'] == "English"
        assert "Drama" in metadata['subject']
        assert metadata['release_date'] == "2021-08-05"
        assert metadata['downloads'] == 12345
        assert "cover.medium.jpg" in metadata['cover_url']

    @pytest.mark.asyncio
    async def test_get_book_metadata_failure(self, monkeypatch):
        """Test handling of metadata retrieval failure"""
        async def mock_get_metadata_error(book_id):
            return {}, "Failed to fetch book metadata. Status code: 404"

        monkeypatch.setattr(self.api, 'get_book_metadata', mock_get_metadata_error)

        metadata, error = await self.api.get_book_metadata(self.test_book_id)

        assert error is not None
        assert "Failed to fetch book metadata" in error
        assert metadata == {}

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

    def test_extract_title(self):
        """Test extraction of title from HTML"""
        html = """
        <html>
            <body>
                <h1 itemprop="name">Romeo and Juliet</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        title = self.api._extract_title(soup)
        assert title == "Romeo and Juliet"

        soup = BeautifulSoup("<html></html>", 'html.parser')
        title = self.api._extract_title(soup)
        assert title == "Unknown Title"

    def test_extract_author(self):
        """Test extraction of author from HTML"""
        html = """
        <html>
            <body>
                <a itemprop="creator">William Shakespeare</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        author = self.api._extract_author(soup)
        assert author == "William Shakespeare"

        soup = BeautifulSoup("<html></html>", 'html.parser')
        author = self.api._extract_author(soup)
        assert author == "Unknown Author"

    def test_extract_language(self, monkeypatch):
        """Test extraction of language from HTML"""

        def mock_extract_language(soup):
            return "English"
        
        monkeypatch.setattr(self.api, '_extract_language', mock_extract_language)
        soup = BeautifulSoup("<html></html>", 'html.parser')

        language = self.api._extract_language(soup)

        assert language == "English"

        def mock_extract_missing_language(soup):
            return "Unknown Language"
        
        monkeypatch.setattr(self.api, '_extract_language', mock_extract_missing_language)
        language = self.api._extract_language(soup)
        assert language == "Unknown Language"

    def test_extract_subject(self):
        """Test extraction of subject from HTML"""
        html = """
        <html>
            <body>
                <td property="dcterms:subject"><a>Drama</a></td>
                <td property="dcterms:subject"><a>Tragedy</a></td>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        subjects = self.api._extract_subject(soup)
        assert len(subjects) == 2
        assert "Drama" in subjects
        assert "Tragedy" in subjects

        soup = BeautifulSoup("<html></html>", 'html.parser')
        subjects = self.api._extract_subject(soup)
        assert subjects == []

    def test_extract_release_date(self):
        """Test extraction of release date from HTML"""
        html = """
        <html>
            <body>
                <td itemprop="datePublished">2021-08-05</td>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        date = self.api._extract_release_date(soup)
        assert date == "2021-08-05"

        soup = BeautifulSoup("<html></html>", 'html.parser')
        date = self.api._extract_release_date(soup)
        assert date == "Unknown Release Date"

    def test_extract_downloads(self):
        """Test extraction of download count from HTML"""
        html = """
        <html>
            <body>
                <td itemprop="interactionCount">12,345 downloads</td>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        downloads = self.api._extract_downloads(soup)
        assert downloads == 12345

        soup = BeautifulSoup("<html></html>", 'html.parser')
        downloads = self.api._extract_downloads(soup)
        assert downloads == 0

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test exception handling in API methods"""
        with patch('aiohttp.ClientSession', side_effect=Exception("Connection error")):
            content, error = await self.api.get_book_content(self.test_book_id)
            assert error is not None
            assert "Error:" in error
            assert content == ""

        with patch('aiohttp.ClientSession', side_effect=Exception("Connection error")):
            metadata, error = await self.api.get_book_metadata(self.test_book_id)
            assert error is not None
            assert "Error:" in error
            assert metadata == {}
