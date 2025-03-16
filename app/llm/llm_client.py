import json
import requests
import os
import sseclient
from flask import current_app
from app.llm.model_factory import LLMFactory

class LLMClient:
    """
    Client for interacting with Large Language Models.
    This class serves as a simple wrapper around the Model Factory.
    It maintains backward compatibility with existing code while
    leveraging the new factory pattern for model selection.
    """
    
    def __init__(self, api_key=None, api_url=None, model=None):
        """
        Initialize the LLM client.
        
        Args:
            api_key (str, optional): API key for the LLM provider
            api_url (str, optional): API URL for the LLM provider
            model (str, optional): Model name to use
        """
        self.model_name = model or os.environ.get('LLM_MODEL') or current_app.config.get('LLM_MODEL', 'gpt-3.5-turbo')
        self.api_key = api_key  # Kept for backward compatibility
        self.api_url = api_url  # Kept for backward compatibility
        
        # Create the appropriate client using the factory
        self.client = LLMFactory.get_llm_client(self.model_name)
    
    def generate_completion(self, prompt, context=None, streaming=False):
        """
        Generate a completion from the LLM.
        
        Args:
            prompt (str): The user's prompt
            context (str, optional): Additional context to provide to the LLM
            streaming (bool, optional): Whether to stream the response
            
        Returns:
            If streaming is False, returns the full response as a string.
            If streaming is True, returns a generator that yields chunks of the response.
        """
        return self.client.generate_completion(prompt, context, streaming)
    
    def _get_full_response(self, headers, payload):
        """Get a full response from the LLM API."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error calling LLM API: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _stream_response(self, headers, payload):
        """Stream a response from the LLM API."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data == "[DONE]":
                    break
                
                try:
                    data = json.loads(event.data)
                    content = data['choices'][0]['delta'].get('content', '')
                    if content:
                        yield content
                except json.JSONDecodeError:
                    current_app.logger.error(f"Error parsing SSE event: {event.data}")
                except KeyError:
                    # Skip events without content
                    pass
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error streaming from LLM API: {str(e)}")
            yield f"Error generating streaming response: {str(e)}" 