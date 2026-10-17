import logging
import time
from typing import Any, Dict, Optional, Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        """
        Returns: (generated_text, tokens_used, model_name_used)
        """
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        # Simulate slight inference network delay
        time.sleep(0.18)
        selected_model = model or "nexus-mock-v1"

        lower = prompt.lower()

        # Weather queries (volatile - real-time data)
        if "weather" in lower:
            if "tokyo" in lower:
                text = "I don't have access to real-time weather data. For current weather in Tokyo, please check weather.com, the Japan Meteorological Agency, or your weather app. Tokyo typically has hot, humid summers (25-35°C) and mild winters (5-12°C) with occasional snow."
            elif "paris" in lower:
                text = "I cannot provide real-time weather information. For current Paris weather, check weather.com or your weather app. Paris has a temperate oceanic climate with mild winters (3-8°C) and warm summers (15-25°C), with rainfall distributed throughout the year."
            elif "new york" in lower or "nyc" in lower:
                text = "I don't have real-time weather access. For current New York weather, visit weather.gov or weather.com. NYC experiences humid subtropical climate with cold winters (0-5°C) and hot, humid summers (22-30°C)."
            else:
                text = "I don't have access to real-time weather data. Please check a weather service like weather.com, Weather Underground, AccuWeather, or your local weather app for current conditions and forecasts."

        # Capital cities
        elif "capital" in lower:
            if "france" in lower or "french" in lower:
                text = "The capital of France is Paris. Located in northern France on the Seine River, Paris is the country's largest city with over 2 million residents in the city proper and 12 million in the metropolitan area. It's renowned as a global center for art, fashion, gastronomy, and culture, featuring iconic landmarks like the Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, and the Arc de Triomphe."
            elif "japan" in lower or "japanese" in lower:
                text = "The capital of Japan is Tokyo. With over 14 million people in the city and 37 million in the greater metropolitan area, Tokyo is one of the world's most populous urban centers. It serves as Japan's political, economic, and cultural hub, blending ancient traditions with cutting-edge technology. Notable landmarks include the Imperial Palace, Senso-ji Temple, Tokyo Tower, and the Shibuya Crossing."
            elif "india" in lower or "indian" in lower:
                text = "The capital of India is New Delhi, which is part of the larger National Capital Territory of Delhi. It serves as the seat of all three branches of the Indian government. The city has a rich history spanning thousands of years and is home to numerous UNESCO World Heritage Sites including Qutub Minar, Humayun's Tomb, and the Red Fort."
            elif "usa" in lower or "united states" in lower or "america" in lower:
                text = "The capital of the United States is Washington, D.C. (District of Columbia). Located on the east coast along the Potomac River, it was established as the nation's capital in 1790. The city is home to all three branches of the U.S. federal government and features iconic monuments like the White House, U.S. Capitol, Lincoln Memorial, and Washington Monument."
            else:
                text = "To help you with capital cities, please specify which country you're asking about. For example: 'What is the capital of France?', 'Tell me about Japan's capital', or 'What's the capital of Brazil?'"

        # Machine Learning / AI
        elif "machine learning" in lower or " ml " in lower or "artificial intelligence" in lower or " ai " in lower:
            text = "Machine Learning (ML) is a subset of artificial intelligence that enables computer systems to learn and improve from experience without being explicitly programmed. ML algorithms analyze data to identify patterns and make predictions or decisions.\n\nKey types include:\n• Supervised Learning: Training with labeled data (e.g., classification, regression)\n• Unsupervised Learning: Finding patterns in unlabeled data (e.g., clustering)\n• Reinforcement Learning: Learning through trial and error with rewards\n\nCommon applications: recommendation systems (Netflix, Spotify), image recognition (facial recognition), natural language processing (ChatGPT, translation), fraud detection, autonomous vehicles, and medical diagnosis."

        # Python code
        elif "python" in lower and ("code" in lower or "function" in lower or "script" in lower or "example" in lower):
            text = """Here's a practical Python example:

```python
def analyze_text(text):
    \"\"\"Analyze text and return statistics\"\"\"
    words = text.lower().split()

    # Count words
    word_count = len(words)

    # Count unique words
    unique_words = len(set(words))

    # Find most common word
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    most_common = max(word_freq, key=word_freq.get) if word_freq else None

    return {
        'total_words': word_count,
        'unique_words': unique_words,
        'most_common_word': most_common,
        'avg_word_length': sum(len(w) for w in words) / word_count if word_count > 0 else 0
    }

# Example usage
sample_text = "Python is great. Python is powerful. Python is versatile."
results = analyze_text(sample_text)
print(f"Analysis: {results}")
```

This function provides text statistics including word count, unique words, and most common word."""

        # Explain/What is
        elif "what is" in lower or "explain" in lower or "tell me about" in lower:
            if "python" in lower:
                text = "Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. It's known for its clear, readable syntax and extensive standard library. Python is widely used in web development (Django, Flask), data science (pandas, NumPy), machine learning (TensorFlow, PyTorch), automation, scientific computing, and more. Its philosophy emphasizes code readability and simplicity."
            elif "react" in lower:
                text = "React is a popular JavaScript library for building user interfaces, developed by Facebook (Meta). It uses a component-based architecture where UIs are built from reusable pieces. React's key features include the Virtual DOM for efficient updates, JSX syntax for writing HTML-like code in JavaScript, one-way data flow, and hooks for managing state and side effects. It's widely used for single-page applications and mobile apps (React Native)."
            elif "blockchain" in lower:
                text = "Blockchain is a distributed ledger technology that records transactions across multiple computers in a way that makes the records difficult to alter retroactively. Each 'block' contains transaction data and is cryptographically linked to the previous block, forming a 'chain'. Key features include decentralization, transparency, immutability, and consensus mechanisms. While famous for cryptocurrencies like Bitcoin, blockchain has applications in supply chain, healthcare, voting systems, and digital identity."
            else:
                text = "Based on your question, I'd be happy to explain. However, to provide the most accurate and helpful information, could you please be more specific about what you'd like to know? For example, if you're asking about a technology, concept, or topic, providing more context will help me give you a better answer."

        # How to
        elif "how to" in lower or "how do i" in lower or "how can i" in lower:
            text = "To help you effectively, I need more details about what you're trying to accomplish. Here's a general approach:\n\n1. Identify the specific goal or problem\n2. Break it down into smaller steps\n3. Research best practices and available tools\n4. Start with a simple implementation\n5. Test and iterate\n\nPlease provide more context about your specific question (e.g., 'How to create a REST API in Python?' or 'How to optimize database queries?') and I can give you detailed guidance."

        # Summarization
        elif "summarize" in lower or "summary" in lower:
            text = "To provide an effective summary, I need the content you'd like summarized. A good summary should:\n\n• Capture the main ideas and key points\n• Omit unnecessary details while preserving essential information\n• Be concise yet comprehensive\n• Maintain the original context and meaning\n\nPlease share the text, article, or document you'd like me to summarize, and I'll create a concise overview for you."

        # Translation
        elif "translate" in lower:
            if "french" in lower:
                text = "I can help with French translations! Example:\n\nEnglish: Hello, how are you? → French: Bonjour, comment allez-vous?\nEnglish: Thank you very much → French: Merci beaucoup\nEnglish: What time is it? → French: Quelle heure est-il?\n\nFor professional translations, I recommend DeepL or working with a native speaker for important documents."
            elif "spanish" in lower:
                text = "¡Puedo ayudarte con traducciones al español! Ejemplo:\n\nEnglish: Hello, how are you? → Spanish: Hola, ¿cómo estás?\nEnglish: Thank you very much → Spanish: Muchas gracias\nEnglish: Where is the bathroom? → Spanish: ¿Dónde está el baño?\n\nFor professional work, consider using DeepL or consulting a native Spanish speaker."
            else:
                text = "I can assist with translations! Please specify:\n• Source language (what language to translate FROM)\n• Target language (what language to translate TO)\n• The text you want translated\n\nFor professional-grade translations, especially for legal or medical documents, I recommend using certified translators or services like DeepL, Google Translate, or professional translation agencies."

        # Math/calculations
        elif any(word in lower for word in ["calculate", "solve", "equation", "math", "algebra"]):
            text = "I can help with mathematics! Common topics include:\n\n• Algebra: Solving equations, factoring, systems of equations\n• Calculus: Derivatives, integrals, limits\n• Statistics: Mean, median, standard deviation, probability\n• Geometry: Area, volume, angles, trigonometry\n\nPlease share the specific problem you'd like help with, and I'll guide you through the solution step by step."

        # Default response - more natural
        else:
            # Try to be more helpful based on common patterns
            if "?" in prompt:
                text = "Thank you for your question. To provide the most accurate and helpful response, I need a bit more context. Could you please provide more details about what you're looking for? This will help me give you specific, actionable information rather than a general answer."
            else:
                text = f"I've received your input about: \"{prompt[:100]}{'...' if len(prompt) > 100 else ''}\"\n\nI'm ready to help! To provide the most useful response, please let me know:\n• What specific information are you looking for?\n• Are you trying to solve a problem, learn a concept, or get a recommendation?\n• Any relevant context that would help me understand your needs better?\n\nFeel free to ask questions about technology, programming, science, general knowledge, or other topics!"

        estimated_tokens = len(prompt.split()) + len(text.split())
        return text, estimated_tokens, selected_model


class HuggingFaceProvider(LLMProvider):
    def __init__(self, token: str | None = None, default_model: str | None = None):
        self.token = token or settings.HF_API_TOKEN
        self.default_model = default_model or settings.HF_MODEL_NAME

    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        selected_model = model or self.default_model
        if not self.token:
            logger.warning("HF_API_TOKEN is not configured. Falling back to MockLLMProvider.")
            return await MockLLMProvider().generate(prompt, selected_model, max_tokens, temperature)

        url = f"https://api-inference.huggingface.co/models/{selected_model}"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": max(0.1, temperature),
                "return_full_text": False
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"Hugging Face API error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Hugging Face API returned status {resp.status_code}: {resp.text}")

                data = resp.json()

                # Parse response - HF can return different formats
                if isinstance(data, list) and len(data) > 0:
                    if "generated_text" in data[0]:
                        out = data[0]["generated_text"]
                    elif "translation_text" in data[0]:
                        out = data[0]["translation_text"]
                    elif "summary_text" in data[0]:
                        out = data[0]["summary_text"]
                    else:
                        out = str(data[0])
                elif isinstance(data, dict):
                    if "generated_text" in data:
                        out = data["generated_text"]
                    elif "translation_text" in data:
                        out = data["translation_text"]
                    elif "summary_text" in data:
                        out = data["summary_text"]
                    else:
                        out = str(data)
                else:
                    out = str(data)

                tokens = len(prompt.split()) + len(out.split())
                return out, tokens, selected_model
        except Exception as e:
            logger.error(f"HuggingFace provider error: {e}")
            raise


class GroqProvider(LLMProvider):
    """Groq - Fast inference with Llama models (Free tier available)"""
    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.default_model = default_model or settings.GROQ_MODEL_NAME

    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        selected_model = model or self.default_model
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not configured. Falling back to MockLLMProvider.")
            return await MockLLMProvider().generate(prompt, selected_model, max_tokens, temperature)

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"Groq API error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Groq API returned status {resp.status_code}: {resp.text}")

                data = resp.json()
                out = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", len(prompt.split()) + len(out.split()))
                return out, tokens, selected_model
        except Exception as e:
            logger.error(f"Groq provider error: {e}")
            raise


class OpenRouterProvider(LLMProvider):
    """OpenRouter - Access to many models including free tier"""
    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.default_model = default_model or settings.OPENROUTER_MODEL_NAME

    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        selected_model = model or self.default_model
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not configured. Falling back to MockLLMProvider.")
            return await MockLLMProvider().generate(prompt, selected_model, max_tokens, temperature)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nexusai.dev",  # Optional: your site URL
            "X-Title": "NexusAI Gateway"  # Optional: your app name
        }
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"OpenRouter API error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"OpenRouter API returned status {resp.status_code}: {resp.text}")

                data = resp.json()
                out = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", len(prompt.split()) + len(out.split()))
                return out, tokens, selected_model
        except Exception as e:
            logger.error(f"OpenRouter provider error: {e}")
            raise


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, base_url: str | None = None, default_model: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OPENAI_MODEL_NAME

    async def generate(self, prompt: str, model: str | None = None, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, int, str]:
        selected_model = model or self.default_model
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not configured. Falling back to MockLLMProvider.")
            return await MockLLMProvider().generate(prompt, selected_model, max_tokens, temperature)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"OpenAI API error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"OpenAI API returned status {resp.status_code}: {resp.text}")

                data = resp.json()
                out = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", len(prompt.split()) + len(out.split()))
                return out, tokens, selected_model
        except Exception as e:
            logger.error(f"OpenAI provider error: {e}")
            raise


class LLMService:
    def __init__(self):
        self.mock_provider = MockLLMProvider()
        self.groq_provider = GroqProvider()
        self.hf_provider = HuggingFaceProvider()
        self.openai_provider = OpenAIProvider()
        self.openrouter_provider = OpenRouterProvider()

    async def execute_inference(
        self,
        prompt: str,
        provider_name: str | None = None,
        model_name: str | None = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> tuple[str, int, str, str]:
        """
        Executes inference against chosen provider.
        Returns: (output_text, tokens_used, model_name, active_provider)
        """
        chosen_provider = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

        if chosen_provider == "groq":
            text, tokens, model = await self.groq_provider.generate(prompt, model_name, max_tokens, temperature)
            return text, tokens, model, "groq"
        elif chosen_provider == "huggingface":
            text, tokens, model = await self.hf_provider.generate(prompt, model_name, max_tokens, temperature)
            return text, tokens, model, "huggingface"
        elif chosen_provider == "openai":
            text, tokens, model = await self.openai_provider.generate(prompt, model_name, max_tokens, temperature)
            return text, tokens, model, "openai"
        elif chosen_provider == "openrouter":
            text, tokens, model = await self.openrouter_provider.generate(prompt, model_name, max_tokens, temperature)
            return text, tokens, model, "openrouter"
        else:
            text, tokens, model = await self.mock_provider.generate(prompt, model_name, max_tokens, temperature)
            return text, tokens, model, "mock"


llm_service = LLMService()
