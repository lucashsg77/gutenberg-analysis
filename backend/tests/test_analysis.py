from unittest.mock import patch, MagicMock
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis import BookAnalyzer

class TestBookAnalyzer:
    """Tests for the BookAnalyzer class"""

    def setup_method(self):
        """Set up before each test"""
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-api-key"}):
            self.analyzer = BookAnalyzer()

        self.sample_content = """
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
        
        self.sample_metadata = {
            "id": "1787",
            "title": "Romeo and Juliet",
            "author": "William Shakespeare",
            "language": "English",
            "subject": ["Drama"],
            "release_date": "2021-08-05",
            "downloads": 12345
        }

    @patch('groq.Client')
    def test_identify_characters(self, mock_client):
        """Test character identification with LLM"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
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
                            }
                        ]
                    })
                )
            )
        ]

        mock_client_instance = mock_client.return_value
        mock_client_instance.chat.completions.create.return_value = mock_response

        self.analyzer.client = mock_client_instance

        result = self.analyzer._identify_characters(self.sample_content, self.sample_metadata)

        assert len(result["characters"]) == 2
        assert result["characters"][0]["name"] == "Romeo"
        assert result["characters"][1]["name"] == "Juliet"
        assert result["characters"][0]["relationships"][0]["character"] == "Juliet"
        assert result["characters"][0]["relationships"][0]["strength"] == 10

    @patch('groq.Client')
    def test_extract_themes_and_sentiment(self, mock_client):
        """Test theme and sentiment extraction with LLM"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "themes": [
                            {"name": "Forbidden Love", "description": "Love that transcends social boundaries"},
                            {"name": "Tragedy", "description": "The inevitable tragic ending"}
                        ],
                        "sentiment": {
                            "overall": "mixed",
                            "analysis": "Starts romantic, ends tragic"
                        },
                        "key_quotes": [
                            {
                                "quote": "But, soft! what light through yonder window breaks?",
                                "speaker": "Romeo",
                                "context": "Romeo sees Juliet on her balcony",
                                "significance": "Shows Romeo's immediate attraction"
                            }
                        ]
                    })
                )
            )
        ]

        mock_client_instance = mock_client.return_value
        mock_client_instance.chat.completions.create.return_value = mock_response

        self.analyzer.client = mock_client_instance

        result = self.analyzer._extract_themes_and_sentiment(self.sample_content, self.sample_metadata)

        assert len(result["themes"]) == 2
        assert result["themes"][0]["name"] == "Forbidden Love"
        assert result["sentiment"]["overall"] == "mixed"
        assert len(result["key_quotes"]) == 1
        assert result["key_quotes"][0]["speaker"] == "Romeo"

    @patch.object(BookAnalyzer, '_identify_characters')
    @patch.object(BookAnalyzer, '_extract_themes_and_sentiment')
    @patch.object(BookAnalyzer, '_build_character_graph')
    def test_analyze_book(self, mock_build_graph, mock_extract_themes, mock_identify_chars):
        """Test the full book analysis process"""
        mock_identify_chars.return_value = {
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
            ]
        }
        
        mock_extract_themes.return_value = {
            "themes": [{"name": "Love", "description": "Description"}],
            "sentiment": {"overall": "mixed", "analysis": "Analysis"},
            "key_quotes": [{"quote": "Quote", "speaker": "Romeo", "context": "Context", "significance": "Significance"}]
        }
        
        mock_build_graph.return_value = {
            "nodes": [{"id": "Romeo", "size": 10, "role": "Main", "description": "Description"}],
            "links": [{"source": "Romeo", "target": "Juliet", "value": 10, "type": "Lover"}]
        }

        result, error = self.analyzer.analyze_book(self.sample_content, self.sample_metadata)

        assert error is None
        assert "characters" in result
        assert "graph" in result
        assert "themes" in result
        assert "sentiment" in result
        assert "key_quotes" in result
        assert len(result["characters"]) == 1
        assert result["characters"][0]["name"] == "Romeo"
        assert len(result["themes"]) == 1
        assert result["themes"][0]["name"] == "Love"

    def test_build_character_graph(self):
        """Test building the character relationship graph"""
        characters_info = {
            "characters": [
                {
                    "name": "Romeo",
                    "role": "Main",
                    "description": "Young man",
                    "relationships": [
                        {"character": "Juliet", "type": "Lover", "strength": 10},
                        {"character": "Mercutio", "type": "Friend", "strength": 8}
                    ]
                },
                {
                    "name": "Juliet",
                    "role": "Main",
                    "description": "Young woman",
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
                },
                {
                    "name": "Nurse",
                    "role": "Supporting",
                    "description": "Juliet's nurse",
                    "relationships": [
                        {"character": "Juliet", "type": "Caretaker", "strength": 7}
                    ]
                }
            ]
        }

        graph_data = self.analyzer._build_character_graph(characters_info)

        assert len(graph_data["nodes"]) == 4
        assert len(graph_data["links"]) == 3

        node_names = [node["id"] for node in graph_data["nodes"]]
        assert "Romeo" in node_names
        assert "Juliet" in node_names
        assert "Mercutio" in node_names
        assert "Nurse" in node_names

        for link in graph_data["links"]:
            if link["source"] == "Romeo" and link["target"] == "Juliet":
                assert link["value"] == 10
                assert link["type"] == "Lover"