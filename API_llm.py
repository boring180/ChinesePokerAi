"""
LLM API Integration for Chinese Poker AI
Uses Alibaba Cloud DashScope (Qwen) API
"""

import json
import os
from typing import List, Dict

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Please install openai: pip install openai")


# Load API key
_API_KEY = None
_client = None


def _load_api_key():
    """Load API key from file"""
    global _API_KEY
    if _API_KEY is None:
        try:
            with open('API_key.json', 'r') as f:
                data = json.load(f)
                _API_KEY = data.get('API_KEY')
        except Exception as e:
            # Try environment variable as fallback
            _API_KEY = os.environ.get('DASHSCOPE_API_KEY')
            if _API_KEY is None:
                raise ValueError(f"Cannot load API key: {e}. Please set API_KEY in API_key.json or DASHSCOPE_API_KEY environment variable.")
    return _API_KEY


def _get_client():
    """Get or create OpenAI client"""
    global _client
    if _client is None:
        api_key = _load_api_key()
        _client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    return _client


def get_llm_reaction(history: List[Dict], prompt: str, model: str = "qwen3.6-plus", 
                     temperature: float = 0.7, max_retries: int = 3) -> str:
    """
    Get LLM response for game interaction.
    
    Args:
        history: List of conversation history dicts with 'role' and 'content'
        prompt: Current prompt/message
        model: Model name (default: qwen-plus)
        temperature: Sampling temperature
        max_retries: Number of retries on failure
    
    Returns:
        LLM response text
    
    Raises:
        Exception: If all retries fail
    """
    print(f"Getting LLM reaction for model: {model}")
    client = _get_client()
    
    # Build messages
    messages = history + [{"role": "user", "content": prompt}]
    
    # Try with retries
    last_error = None
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                extra_body={"enable_thinking": False},
                temperature=temperature,
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
    
    # All retries failed
    raise Exception(f"LLM API failed after {max_retries} attempts: {last_error}")


def test_api_connection():
    """Test API connection with a simple query"""
    try:
        response = get_llm_reaction(
            [{"role": "system", "content": "You are a helpful assistant."}],
            "Say 'API connection successful!' and nothing else.",
            temperature=0.1
        )
        print(f"✓ API Test: {response.strip()}")
        return True
    except Exception as e:
        print(f"✗ API Test Failed: {e}")
        return False


# For testing when run directly
if __name__ == "__main__":
    print("Testing LLM API connection...")
    success = test_api_connection()
    if success:
        print("\n✓ API is working correctly!")
    else:
        print("\n✗ Please check your API key and network connection.")
        print("  1. Verify API_key.json contains a valid key")
        print("  2. Check network connectivity to dashscope.aliyuncs.com")
