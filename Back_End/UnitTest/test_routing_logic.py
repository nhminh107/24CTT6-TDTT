import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys

# Add the project root to sys.path to import Back_End
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")

from Back_End.Core.QA_Chatbot import ChatBot

class TestChatBotRouting(unittest.IsolatedAsyncioTestCase):
    @patch('Back_End.Core.QA_Chatbot._client')
    async def test_routing_search_good_info(self, mock_client):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({"user_intent": "Search", "isPoorInfo": 0})))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('Back_End.Core.QA_Chatbot._client', mock_client):
            chatbot = ChatBot()
            result = await chatbot.routing("Tìm quán ăn sáng ngon ở Quận 1")
            
            data = json.loads(result)
            self.assertEqual(data["user_intent"], "Search")
            self.assertEqual(data["isPoorInfo"], 0)

    @patch('Back_End.Core.QA_Chatbot._client')
    async def test_routing_search_poor_info(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({"user_intent": "Search", "isPoorInfo": 1})))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('Back_End.Core.QA_Chatbot._client', mock_client):
            chatbot = ChatBot()
            result = await chatbot.routing("cay")
            
            data = json.loads(result)
            self.assertEqual(data["user_intent"], "Search")
            self.assertEqual(data["isPoorInfo"], 1)

    @patch('Back_End.Core.QA_Chatbot._client')
    async def test_routing_qa(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({"user_intent": "QA"})))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('Back_End.Core.QA_Chatbot._client', mock_client):
            chatbot = ChatBot()
            result = await chatbot.routing("Ăn nhiều đường có tốt cho sức khỏe không?")
            
            data = json.loads(result)
            self.assertEqual(data["user_intent"], "QA")

if __name__ == '__main__':
    unittest.main()
