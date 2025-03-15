import unittest
import json
import sseclient
import requests
import os
from flask import url_for
from app import create_app
from app.models.dynamic import db

class SSETestCase(unittest.TestCase):
    """Test case for the SSE endpoint."""
    
    def setUp(self):
        """Set up the test environment."""
        # Use the testing configuration
        os.environ['FLASK_ENV'] = 'testing'
        
        self.app = create_app()
        self.client = self.app.test_client()
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Set up mock LLM environment
        os.environ['LLM_API_KEY'] = 'test-key'
        os.environ['LLM_MODEL'] = 'test-model'
    
    def tearDown(self):
        """Tear down the test environment."""
        self.app_context.pop()
    
    def test_sse_endpoint_exists(self):
        """Test that the SSE endpoint exists."""
        with self.app.test_request_context():
            url = url_for('sse.stream_llm_response')
            
            # Check that the route exists
            self.assertEqual(url, '/sse/llm')
    
    def test_sse_requires_prompt(self):
        """Test that the SSE endpoint requires a prompt."""
        response = self.client.post('/sse/llm', 
                                   data=json.dumps({}),
                                   content_type='application/json')
        
        # Should return a 400 if no prompt is provided
        self.assertEqual(response.status_code, 400)
        
        # Check the error message in the SSE response
        data = json.loads(response.data.decode('utf-8').split('\n')[1].replace('data: ', ''))
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main() 