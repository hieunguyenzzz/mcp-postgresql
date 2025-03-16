"""
Model Factory module for handling different LLM providers.
This module implements a factory pattern to create and manage different LLM client implementations.
"""

import os
import json
import requests
import sseclient
from abc import ABC, abstractmethod
from flask import current_app

class BaseLLMClient(ABC):
    """Base abstract class for LLM clients."""
    
    @abstractmethod
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
        pass


class OpenAIClient(BaseLLMClient):
    """Client for interacting with OpenAI compatible APIs."""
    
    def __init__(self, model=None, api_key=None, api_url=None):
        """Initialize the OpenAI client."""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or current_app.config.get('OPENAI_API_KEY')
        # Fall back to general LLM keys if specific ones not provided
        if not self.api_key:
            self.api_key = os.environ.get('LLM_API_KEY') or current_app.config.get('LLM_API_KEY')
            
        self.api_url = api_url or os.environ.get('OPENAI_API_URL') or current_app.config.get('OPENAI_API_URL')
        if not self.api_url:
            self.api_url = "https://api.openai.com/v1/chat/completions"
            
        self.model = model or os.environ.get('OPENAI_MODEL') or current_app.config.get('OPENAI_MODEL')
        if not self.model:
            self.model = os.environ.get('LLM_MODEL') or current_app.config.get('LLM_MODEL', 'gpt-3.5-turbo')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def generate_completion(self, prompt, context=None, streaming=False):
        """Generate a completion from the OpenAI API."""
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
        """Get a full response from the OpenAI API."""
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
            current_app.logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _stream_response(self, headers, payload):
        """Stream a response from the OpenAI API."""
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
            current_app.logger.error(f"Error streaming from OpenAI API: {str(e)}")
            yield f"Error generating streaming response: {str(e)}"


class OllamaClient(BaseLLMClient):
    """Client for interacting with Ollama API."""
    
    def __init__(self, model=None, api_url=None):
        """Initialize the Ollama client."""
        self.api_url = api_url or os.environ.get('OLLAMA_API_URL') or current_app.config.get('OLLAMA_API_URL')
        if not self.api_url:
            # Default Ollama endpoint
            self.api_url = "http://localhost:11434/api/generate"
            
        self.model = model or os.environ.get('OLLAMA_MODEL') or current_app.config.get('OLLAMA_MODEL')
        if not self.model:
            self.model = "llama2"  # Default Ollama model
    
    def generate_completion(self, prompt, context=None, streaming=False):
        """Generate a completion from the Ollama API."""
        system_prompt = ""
        if context:
            system_prompt = f"You are an assistant with access to database information. Use this database context to help answer questions: {context}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": streaming
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if streaming:
            # Return a generator for streaming responses
            return self._stream_response(headers, payload)
        else:
            # Return the full response for non-streaming
            return self._get_full_response(headers, payload)
    
    def _get_full_response(self, headers, payload):
        """Get a full response from the Ollama API."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            response_json = response.json()
            return response_json.get('response', '')
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error calling Ollama API: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _stream_response(self, headers, payload):
        """Stream a response from the Ollama API."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                    if data.get('done', False):
                        break
                except json.JSONDecodeError:
                    current_app.logger.error(f"Error parsing Ollama response: {line}")
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error streaming from Ollama API: {str(e)}")
            yield f"Error generating streaming response: {str(e)}"


class LLMFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def get_llm_client(model_name=None):
        """
        Get the appropriate LLM client based on model name.
        
        Args:
            model_name (str, optional): The name of the model to use
            
        Returns:
            An instance of a BaseLLMClient implementation
        """
        if not model_name:
            # Get default model from config
            model_name = current_app.config.get('DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
        
        # Check model provider based on prefix or model name convention
        if model_name.startswith(('gpt', 'text-davinci', 'davinci')):
            return OpenAIClient(model=model_name)
        elif model_name in ['claude', 'claude-2', 'claude-instant'] or model_name.startswith('claude'):
            # For future Anthropic support
            raise NotImplementedError(f"Support for {model_name} not yet implemented")
        elif model_name in ['mistral', 'llama', 'llama2', 'codellama'] or model_name.startswith(('mistral', 'llama')):
            return OllamaClient(model=model_name)
        else:
            # Default to OpenAI
            current_app.logger.warning(f"Unknown model: {model_name}, defaulting to OpenAI client")
            return OpenAIClient(model=model_name) 