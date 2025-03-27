import os
import json
import groq
import nltk
import networkx as nx
import asyncio
import time
from typing import AsyncGenerator, Dict, Tuple, Any, Optional
from dotenv import load_dotenv

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

load_dotenv()

class BookAnalyzer:
    """
    A class to analyze book content using LLM and extract character information
    """
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = groq.Client(api_key=api_key)
        self.model = "llama3-70b-8192"

    async def analyze_book_incremental(self, book_content: str, book_metadata: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Analyze book content incrementally, yielding partial results as they become available
        
        Args:
            book_content: Cleaned book content
            book_metadata: Book metadata
            
        Yields:
            Partial analysis results with status updates
        """
        overall_start_time = time.time()
        
        try:
            sample_size = min(len(book_content), 30000)
            beginning = book_content[:sample_size // 3]
            middle_start = max(0, len(book_content) // 2 - sample_size // 6)
            middle = book_content[middle_start:middle_start + sample_size // 3]
            end_start = max(0, len(book_content) - sample_size // 3)
            end = book_content[end_start:]
            sample_text = beginning + middle + end

            yield {
                "status": "processing",
                "progress": 5,
                "message": "Analyzing book structure...",
                "stage": "initialization",
                "partial_results": {
                    "characters": []
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 10,
                "message": "Starting character identification...",
                "stage": "character_analysis_prep",
                "partial_results": {
                    "characters": []
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 20,
                "message": "Identifying characters and relationships...",
                "stage": "character_analysis_in_progress",
                "partial_results": {
                    "characters": []
                }
            }

            characters_info = await self._identify_characters_streaming(sample_text, book_metadata)

            yield {
                "status": "processing",
                "progress": 40,
                "message": f"Characters identified ({len(characters_info.get('characters', []))} found)",
                "stage": "character_analysis_complete",
                "partial_results": {
                    "characters": characters_info.get("characters", [])
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 50,
                "message": "Building character network...",
                "stage": "graph_generation_started",
                "partial_results": {
                    "characters": characters_info.get("characters", [])
                }
            }

            graph_data = self._build_character_graph(characters_info)

            yield {
                "status": "processing",
                "progress": 60,
                "message": "Character network visualization ready",
                "stage": "graph_generation",
                "partial_results": {
                    "characters": characters_info.get("characters", []),
                    "graph": graph_data
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 70,
                "message": "Starting theme and sentiment analysis...",
                "stage": "theme_analysis_started",
                "partial_results": {
                    "characters": characters_info.get("characters", []),
                    "graph": graph_data
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 80,
                "message": "Extracting themes, sentiment, and key quotes...",
                "stage": "theme_analysis_in_progress",
                "partial_results": {
                    "characters": characters_info.get("characters", []),
                    "graph": graph_data
                }
            }

            themes_and_sentiment = await self._extract_themes_and_sentiment_streaming(sample_text, book_metadata)

            yield {
                "status": "processing",
                "progress": 90,
                "message": "Themes and quotes extracted",
                "stage": "theme_analysis_complete",
                "partial_results": {
                    "characters": characters_info.get("characters", []),
                    "graph": graph_data,
                    "themes": themes_and_sentiment.get("themes", []),
                    "sentiment": themes_and_sentiment.get("sentiment", {}),
                    "key_quotes": themes_and_sentiment.get("key_quotes", [])
                }
            }

            await asyncio.sleep(0.1)

            yield {
                "status": "processing",
                "progress": 95,
                "message": "Finalizing analysis...",
                "stage": "finalization",
                "partial_results": {
                    "characters": characters_info.get("characters", []),
                    "graph": graph_data,
                    "themes": themes_and_sentiment.get("themes", []),
                    "sentiment": themes_and_sentiment.get("sentiment", {}),
                    "key_quotes": themes_and_sentiment.get("key_quotes", [])
                }
            }

            analysis_results = {
                "characters": characters_info.get("characters", []),
                "graph": graph_data,
                "themes": themes_and_sentiment.get("themes", []),
                "sentiment": themes_and_sentiment.get("sentiment", {}),
                "key_quotes": themes_and_sentiment.get("key_quotes", [])
            }
            
            overall_duration = time.time() - overall_start_time


            yield {
                "status": "complete",
                "progress": 100,
                "message": f"Analysis complete ({overall_duration:.1f} seconds)",
                "stage": "complete",
                "partial_results": analysis_results
            }
            
        except Exception as e:

            yield {
                "status": "error",
                "message": f"Error in book analysis: {str(e)}"
            }

    async def _identify_characters_streaming(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Streaming version of character identification"""
        prompt = self._create_character_prompt(text, metadata)
 
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4000,
                stream=True
            )
            
            response_text = ""
            chunk_count = 0
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        chunk_count += 1
            
            return self._parse_json_response(response_text, "characters")
        except Exception as e:

            return await self._identify_characters_async(text, metadata)
    
    async def _extract_themes_and_sentiment_streaming(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Streaming version of theme and sentiment extraction"""
        prompt = self._create_themes_prompt(text, metadata)
  
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
                stream=True
            )
            
            response_text = ""
            chunk_count = 0
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        chunk_count += 1
                      
            return self._parse_json_response(response_text, "themes")
        except Exception as e:
            return await self._extract_themes_and_sentiment_async(text, metadata)

    async def _identify_characters_async(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of character identification without streaming"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._identify_characters, text, metadata)

    async def _extract_themes_and_sentiment_async(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of theme and sentiment extraction without streaming"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_themes_and_sentiment, text, metadata)

    def analyze_book(self, book_content: str, book_metadata: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Analyze book content to extract character information and relationships
        
        Args:
            book_content: Cleaned book content
            book_metadata: Book metadata
            
        Returns:
            Tuple containing:
                - Analysis results dictionary
                - Error message (if any)
        """
        try:

            sample_size = min(len(book_content), 30000)
            beginning = book_content[:sample_size // 3]
            middle_start = max(0, len(book_content) // 2 - sample_size // 6)
            middle = book_content[middle_start:middle_start + sample_size // 3]
            end_start = max(0, len(book_content) - sample_size // 3)
            end = book_content[end_start:]
            
            sample_text = beginning + middle + end

            characters_info = self._identify_characters(sample_text, book_metadata)

            graph_data = self._build_character_graph(characters_info)

            themes_and_sentiment = self._extract_themes_and_sentiment(sample_text, book_metadata)

            analysis_results = {
                "characters": characters_info.get("characters", []),
                "graph": graph_data,
                "themes": themes_and_sentiment.get("themes", []),
                "sentiment": themes_and_sentiment.get("sentiment", {}),
                "key_quotes": themes_and_sentiment.get("key_quotes", [])
            }
               
            return analysis_results, None
        except Exception as e:

            return {}, f"Error in book analysis: {str(e)}"
    
    def _create_character_prompt(self, text: str, metadata: Dict[str, Any]) -> str:
        """Create the prompt for character identification"""
        return f"""
        You are a literary analyst. Based on the provided text from the book "{metadata.get('title', 'Unknown')}" 
        by {metadata.get('author', 'Unknown Author')}, identify the following:

        1. Main and supporting characters in the text
        2. For each character, provide:
           - Their name and any aliases
           - Their role in the story
           - Brief description
           - Key relationships with other characters
        
        Respond in JSON format only, with the following structure:
        {{
          "characters": [
            {{
              "name": "Character Name",
              "aliases": ["Alias1", "Alias2"],
              "role": "Main/Supporting/Minor",
              "description": "Brief description",
              "relationships": [
                {{"character": "Related Character Name", "type": "Relationship Type", "strength": 1-10}}
              ]
            }}
          ]
        }}
        
        The strength value (1-10) represents how strongly connected the characters are.
        
        Here's the text sample:
        
        {text[:5000]}
        
        [Text continued in middle section...]
        
        {text[len(text)//2-2500:len(text)//2+2500]}
        
        [Text continued in end section...]
        
        {text[-5000:]}
        """

    def _create_themes_prompt(self, text: str, metadata: Dict[str, Any]) -> str:
        """Create the prompt for themes and sentiment extraction"""
        return f"""
        You are a literary analyst. Based on the provided text from the book "{metadata.get('title', 'Unknown')}" 
        by {metadata.get('author', 'Unknown Author')}, identify the following:

        1. Key themes in the text (3-5 major themes)
        2. Overall sentiment analysis of the text
        3. Extract 5 significant quotes with attribution and context
        
        Respond in JSON format only, with the following structure:
        {{
          "themes": [
            {{"name": "Theme Name", "description": "Theme Description"}}
          ],
          "sentiment": {{
            "overall": "positive/negative/neutral/mixed",
            "analysis": "Brief analysis of the emotional tone"
          }},
          "key_quotes": [
            {{
              "quote": "The quote text",
              "speaker": "Character who spoke it (if applicable)",
              "context": "Brief context for the quote",
              "significance": "Why this quote is important"
            }}
          ]
        }}
        
        Here's the text sample:
        
        {text[:5000]}
        
        [Text continued in middle section...]
        
        {text[len(text)//2-2500:len(text)//2+2500]}
        
        [Text continued in end section...]
        
        {text[-5000:]}
        """

    def _identify_characters(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to identify characters and their relationships
        
        Args:
            text: Sample of book content
            metadata: Book metadata
            
        Returns:
            Dictionary with characters information
        """
        prompt = self._create_character_prompt(text, metadata)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content.strip()

        return self._parse_json_response(response_text, "characters")

    def _parse_json_response(self, response_text: str, expected_key: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > 0:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                if expected_key in result:
                    return result
                else:
        
                    if expected_key == "characters":
                        return {"characters": []}
                    elif expected_key == "themes":
                        return {"themes": [], "sentiment": {}, "key_quotes": []}

            if expected_key == "characters":
                return {"characters": []}
            elif expected_key == "themes":
                return {"themes": [], "sentiment": {}, "key_quotes": []}
        except json.JSONDecodeError as e:

            if expected_key == "characters":
                return {"characters": []}
            elif expected_key == "themes":
                return {"themes": [], "sentiment": {}, "key_quotes": []}

    def _build_character_graph(self, characters_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a network graph from character relationships
        
        Args:
            characters_info: Dictionary with characters information
            
        Returns:
            Graph data for visualization
        """
        characters = characters_info.get("characters", [])

        G = nx.Graph()

        for character in characters:
            relationship_count = len(character.get("relationships", []))
            node_size = 10 + (relationship_count * 2)

            G.add_node(
                character["name"], 
                size=node_size,
                role=character.get("role", "Unknown"),
                description=character.get("description", "")
            )

        edge_count = 0
        for character in characters:
            for relationship in character.get("relationships", []):
                related_character = relationship.get("character")

                if related_character in G:
                    if not G.has_edge(character["name"], related_character):
                        strength = relationship.get("strength", 5)
                        relationship_type = relationship.get("type", "Unknown")

                        G.add_edge(
                            character["name"],
                            related_character,
                            weight=strength,
                            type=relationship_type
                        )
                        edge_count += 1

        nodes = []
        for node, attrs in G.nodes(data=True):
            nodes.append({
                "id": node,
                "size": attrs.get("size", 10),
                "role": attrs.get("role", "Unknown"),
                "description": attrs.get("description", "")
            })
        
        links = []
        for source, target, attrs in G.edges(data=True):
            links.append({
                "source": source,
                "target": target,
                "value": attrs.get("weight", 1),
                "type": attrs.get("type", "Unknown")
            })
        
        graph_data = {
            "nodes": nodes,
            "links": links
        }
        
        return graph_data

    def _extract_themes_and_sentiment(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to extract key themes, sentiment, and quotes
        
        Args:
            text: Sample of book content
            metadata: Book metadata
            
        Returns:
            Dictionary with themes, sentiment, and key quotes
        """
        prompt = self._create_themes_prompt(text, metadata)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()

        return self._parse_json_response(response_text, "themes")