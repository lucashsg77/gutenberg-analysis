import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, Any, Tuple, Optional

class GutenbergAPI:
    """
    A class to interact with Project Gutenberg API to fetch book content and metadata
    """
    def __init__(self):
        self.base_url = "https://www.gutenberg.org"
    
    async def get_book_content(self, book_id: str) -> Tuple[str, Optional[str]]:
        """
        Fetch book content from Project Gutenberg asynchronously
        
        Args:
            book_id: The ID of the book on Project Gutenberg
            
        Returns:
            Tuple containing:
                - Book content
                - Error message (if any)
        """
        try:
            async with aiohttp.ClientSession() as session:
                urls = [
                    f"{self.base_url}/files/{book_id}/{book_id}-0.txt",
                    f"{self.base_url}/cache/epub/{book_id}/pg{book_id}.txt",
                    f"{self.base_url}/ebooks/{book_id}.txt.utf-8"
                ]

                tasks = []
                for url in urls:
                    tasks.append(self._try_url(session, url))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, tuple) and result[0]:
                        return result[0], None

                return "", "Failed to fetch book content from any URL"
        except Exception as e:
        
            return "", f"Error: {str(e)}"
    
    async def _try_url(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, Optional[str]]:
        """Helper method to try a single URL"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                
                    return content, None
                else:
                
                    return "", f"Status {response.status}"
        except Exception as e:
        
            return "", str(e)

    async def get_book_metadata(self, book_id: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Fetch book metadata from Project Gutenberg asynchronously
        
        Args:
            book_id: The ID of the book on Project Gutenberg
            
        Returns:
            Tuple containing:
                - Dictionary with book metadata
                - Error message (if any)
        """
        try:
            async with aiohttp.ClientSession() as session:
                metadata_url = f"{self.base_url}/ebooks/{book_id}"
            
                
                async with session.get(metadata_url, timeout=10) as response:
                    if response.status != 200:
                    
                        return {}, f"Failed to fetch book metadata. Status code: {response.status}"
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    metadata = {
                        "id": book_id,
                        "title": self._extract_title(soup),
                        "author": self._extract_author(soup),
                        "language": self._extract_language(soup),
                        "subject": self._extract_subject(soup),
                        "release_date": self._extract_release_date(soup),
                        "downloads": self._extract_downloads(soup),
                        "cover_url": self._extract_cover_url(soup, book_id)
                    }
                    return metadata, None
        except Exception as e:
        
            return {}, f"Error: {str(e)}"

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the metadata page"""
        title_element = soup.select_one('h1[itemprop="name"]')
        if title_element:
            return title_element.text.strip()
        return "Unknown Title"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract the author from the metadata page"""
        author_element = soup.select_one('a[itemprop="creator"]')
        if author_element:
            return author_element.text.strip()
        return "Unknown Author"
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract the language from the metadata page"""
        language_element = soup.select_one('tr:contains("Language") td')
        if language_element:
            return language_element.text.strip()
        return "Unknown Language"
    
    def _extract_subject(self, soup: BeautifulSoup) -> list:
        """Extract the subject from the metadata page"""
        subject_elements = soup.select('td[property="dcterms:subject"] a')
        if subject_elements:
            return [subject.text.strip() for subject in subject_elements]
        return []
    
    def _extract_release_date(self, soup: BeautifulSoup) -> str:
        """Extract the release date from the metadata page"""
        release_date_element = soup.select_one('td[itemprop="datePublished"]')
        if release_date_element:
            return release_date_element.text.strip()
        return "Unknown Release Date"
    
    def _extract_downloads(self, soup: BeautifulSoup) -> int:
        """Extract the download count from the metadata page"""
        downloads_text = soup.select_one('td[itemprop="interactionCount"]')
        if downloads_text:
            downloads_str = downloads_text.text.strip()
            numbers = re.findall(r'\d+', downloads_str)
            if numbers:
                return int(''.join(numbers))
        return 0
    
    def _extract_cover_url(self, soup: BeautifulSoup, book_id: str) -> str:
        """Extract the cover image URL if available"""
        img_element = soup.select_one('img[src*="cover"]')
        if img_element and 'src' in img_element.attrs:
            src = img_element['src']
            if src.startswith('/'):
                return f"{self.base_url}{src}"
            return src

        return f"{self.base_url}/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"
    
    def clean_book_content(self, content: str) -> str:
        """
        Clean the book content by removing Project Gutenberg headers and footers.
        
        Args:
            content: Raw book content
            
        Returns:
            Cleaned book content
        """
        start_time = time.time()
    
        
        start_markers = [
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "*** START OF THE PROJECT GUTENBERG EBOOK",
            "*END*THE SMALL PRINT",
            "*** START OF THE PROJECT GUTENBERG",
            "This eBook is for the use of anyone anywhere"
        ]
        
        end_markers = [
            "*** END OF THIS PROJECT GUTENBERG EBOOK",
            "*** END OF THE PROJECT GUTENBERG EBOOK",
            "End of Project Gutenberg's",
            "End of the Project Gutenberg",
            "End of Project Gutenberg"
        ]

        start_marker_pos = -1
        for marker in start_markers:
            pos = content.find(marker)
            if pos != -1 and (start_marker_pos == -1 or pos < start_marker_pos):
                start_marker_pos = pos

        if start_marker_pos != -1:
            line_end = content.find("\n", start_marker_pos)
            if line_end != -1:
                content = content[line_end + 1:]

        end_marker_pos = -1
        for marker in end_markers:
            pos = content.rfind(marker)
            if pos != -1 and (end_marker_pos == -1 or pos < end_marker_pos):
                end_marker_pos = pos

        if end_marker_pos != -1:
            line_start = content.rfind("\n", 0, end_marker_pos)
            if line_start != -1:
                content = content[:line_start]

        cleaned_lines = []
        for line in content.split("\n"):
            if "Project Gutenberg" not in line and "www.gutenberg.org" not in line:
                cleaned_lines.append(line)
        
        cleaned_content = "\n".join(cleaned_lines)
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content if len(cleaned_content) > 100 else ""
