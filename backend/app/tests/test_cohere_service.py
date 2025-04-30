import unittest
from unittest.mock import patch, MagicMock
import requests
import json
from app.services.cohere_service import CohereService
from app.core.config import settings

class TestCohereService(unittest.TestCase):
    """Test cases for the Cohere service implementation."""

    @patch('requests.post')
    def test_successful_summary(self, mock_post):
        """Test successful summary generation with the Cohere API."""
        # Mock the response from Cohere API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "summary": "This is a test summary.",
            "id": "12345"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the service
        result = CohereService.get_summary("This is a test text that needs to be summarized.")

        # Verify the result
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("summary"), "This is a test summary.")
        self.assertIn("stats", result)
        self.assertIn("input_tokens", result["stats"])
        self.assertIn("output_tokens", result["stats"])
        self.assertIn("processing_time_ms", result["stats"])

        # Verify API call
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs['headers']['Content-Type'], 'application/json')
        self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {settings.COHERE_API_KEY}")
        payload = kwargs['json']
        self.assertEqual(payload['model'], CohereService.DEFAULT_MODEL)
        self.assertEqual(payload['length'], 'short')
        self.assertEqual(payload['format'], 'paragraph')
        self.assertEqual(payload['extractiveness'], 'high')
        self.assertEqual(payload['temperature'], 0.3)

    @patch('requests.post')
    def test_failed_summary_http_error(self, mock_post):
        """Test handling of HTTP errors from the Cohere API."""
        # Mock HTTP error
        http_error = requests.exceptions.HTTPError()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = http_error
        http_error.response = mock_response  # Set the response attribute on the error
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        # Call the service
        result = CohereService.get_summary("This is a test text.")

        # Verify the result
        self.assertFalse(result.get("success"))
        self.assertIn("error", result)

    @patch('requests.post')
    def test_retry_on_timeout(self, mock_post):
        """Test retry logic on timeout errors."""
        # First call times out, second one succeeds
        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            MagicMock(
                json=lambda: {"summary": "Retry succeeded"}, 
                raise_for_status=lambda: None
            )
        ]

        # Call the service with reduced wait time for faster testing
        result = CohereService.get_summary("Test text", wait_time=0.1)

        # Verify the result
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("summary"), "Retry succeeded")
        self.assertEqual(mock_post.call_count, 2)  # Verify it was called twice

    @patch('requests.post')
    def test_too_many_retries_fails(self, mock_post):
        """Test that the service gives up after max retries."""
        # All calls time out
        mock_post.side_effect = requests.exceptions.Timeout()

        # Call the service with reduced wait time for faster testing
        result = CohereService.get_summary("Test text", retry_count=2, wait_time=0.1)

        # Verify the result
        self.assertFalse(result.get("success"))
        self.assertIn("error", result)
        self.assertEqual(mock_post.call_count, 2)  # Verify it was called twice

if __name__ == '__main__':
    unittest.main()