import json
import requests
import os
import sseclient
from flask import current_app

class LLMClient:
    """Client for interacting with Large Language Model APIs."""
    
    def __init__(self, api_key=None, api_url=None, model=None):
        """Initialize the LLM client."""
        self.api_key = api_key or os.environ.get('LLM_API_KEY') or current_app.config.get('LLM_API_KEY')
        self.api_url = api_url or os.environ.get('LLM_API_URL') or current_app.config.get('LLM_API_URL')
        self.model = model or os.environ.get('LLM_MODEL') or current_app.config.get('LLM_MODEL')
        
        if not self.api_key:
            raise ValueError("LLM API key is required")
        
        if not self.api_url:
            # Default to OpenAI-compatible API endpoint
            self.api_url = "https://api.openai.com/v1/chat/completions"
    
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
        messages = []
        
        # Add system message with context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"You are an assistant with access to database information. Use this database context to help answer questions: {context}"
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are an assistant that helps answer questions."
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": streaming
        }
        
        if streaming:
            # Return a generator for streaming responses
            return self._stream_response(headers, payload)
        else:
            # Return the full response for non-streaming
            return self._get_full_response(headers, payload)
    
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