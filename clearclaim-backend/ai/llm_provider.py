import os
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def answer(self, system_prompt: str, messages: list) -> str:
        pass

class AnthropicProvider(LLMProvider):
    def __init__(self):
        import anthropic
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please set it to use Claude.")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def answer(self, system_prompt: str, messages: list) -> str:
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text

class OpenAIProvider(LLMProvider):
    def __init__(self):
        import openai
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it to use GPT-4o.")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def answer(self, system_prompt: str, messages: list) -> str:
        oai_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=oai_messages,
            max_tokens=1000
        )
        return response.choices[0].message.content

class GeminiProvider(LLMProvider):
    def __init__(self):
        import google.generativeai as genai
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it to use Gemini.")
        genai.configure(api_key=self.api_key)

    async def answer(self, system_prompt: str, messages: list) -> str:
        import google.generativeai as genai
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
        
        gemini_messages = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})
            
        response = await model.generate_content_async(gemini_messages)
        return response.text

def get_llm_provider(provider_name: str = None) -> LLMProvider:
    provider_name = provider_name or os.getenv("LLM_PROVIDER", "anthropic")
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        return AnthropicProvider()