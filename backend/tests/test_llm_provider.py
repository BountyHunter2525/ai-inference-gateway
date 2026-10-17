"""
Tests for app/services/llm_provider.py

MockLLMProvider    — all keyword branches, default branch, token counting
HuggingFaceProvider — no-token fallback, HTTP 200 (list & dict responses),
                      HTTP error raises RuntimeError
OpenAIProvider     — no-key fallback, HTTP 200 with usage field,
                      HTTP 200 without usage field, HTTP error raises RuntimeError
LLMService         — provider routing (mock / huggingface / openai / unknown)

HTTP calls are intercepted with pytest-httpx (respx alternative that works
with httpx natively). We mock at the httpx transport level so no real network
traffic is needed.
"""

import json

import pytest
import pytest_asyncio

# ── async test helper ─────────────────────────────────────────────────────────
# All provider methods are async, so we need an event loop.
# pytest-asyncio is already a transitive dep of httpx[test]; mark tests with
# @pytest.mark.asyncio and ensure asyncio_mode = "auto" is set (or mark inline).

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════════════════════
# MockLLMProvider
# ═══════════════════════════════════════════════════════════════════════════════

class TestMockLLMProvider:
    @pytest.fixture()
    def provider(self):
        from app.services.llm_provider import MockLLMProvider
        return MockLLMProvider()

    async def test_capital_france_branch(self, provider):
        text, tokens, model = await provider.generate("What is the capital of France?")
        assert "Paris" in text
        assert tokens > 0
        assert model == "nexus-mock-v1"

    async def test_summarize_branch(self, provider):
        text, tokens, model = await provider.generate("Please summarize this article")
        assert "Summary" in text

    async def test_translate_branch(self, provider):
        text, tokens, model = await provider.generate("Translate this text to Spanish")
        assert "Translation" in text

    async def test_code_branch(self, provider):
        text, tokens, model = await provider.generate("Write Python code to sort a list")
        assert "python" in text.lower() or "def" in text or "```" in text

    async def test_default_branch(self, provider):
        text, tokens, model = await provider.generate("Explain the big bang theory")
        assert "NexusAI Inference Result" in text

    async def test_custom_model_name_respected(self, provider):
        _, _, model = await provider.generate("hello", model="my-custom-model")
        assert model == "my-custom-model"

    async def test_token_count_is_positive(self, provider):
        _, tokens, _ = await provider.generate("How does TCP work?")
        assert tokens > 0

    async def test_default_model_name_when_none(self, provider):
        _, _, model = await provider.generate("test", model=None)
        assert model == "nexus-mock-v1"


# ═══════════════════════════════════════════════════════════════════════════════
# HuggingFaceProvider
# ═══════════════════════════════════════════════════════════════════════════════

class TestHuggingFaceProvider:
    @pytest.fixture()
    def provider_no_token(self):
        from app.services.llm_provider import HuggingFaceProvider
        return HuggingFaceProvider(token=None)

    @pytest.fixture()
    def provider_with_token(self):
        from app.services.llm_provider import HuggingFaceProvider
        return HuggingFaceProvider(token="hf-fake-token-abc123")

    async def test_no_token_falls_back_to_mock(self, provider_no_token):
        text, tokens, model = await provider_no_token.generate("What is the capital of France?")
        assert "Paris" in text
        assert tokens > 0

    async def test_http_200_list_response(self, provider_with_token, respx_mock):
        import httpx
        respx_mock.post("https://api-inference.huggingface.co/models/google/flan-t5-base").mock(
            return_value=httpx.Response(
                200,
                json=[{"generated_text": "The answer is 42."}],
            )
        )
        text, tokens, model = await provider_with_token.generate("What is the answer?")
        assert text == "The answer is 42."
        assert tokens > 0

    async def test_http_200_dict_response(self, provider_with_token, respx_mock):
        import httpx
        respx_mock.post("https://api-inference.huggingface.co/models/google/flan-t5-base").mock(
            return_value=httpx.Response(
                200,
                json={"generated_text": "Dict response text."},
            )
        )
        text, tokens, model = await provider_with_token.generate("Test dict response")
        assert text == "Dict response text."

    async def test_http_200_unknown_shape_returns_str(self, provider_with_token, respx_mock):
        import httpx
        raw_data = {"unexpected": "shape"}
        respx_mock.post("https://api-inference.huggingface.co/models/google/flan-t5-base").mock(
            return_value=httpx.Response(200, json=raw_data)
        )
        text, tokens, model = await provider_with_token.generate("Test unknown shape")
        assert isinstance(text, str)
        assert len(text) > 0

    async def test_http_error_raises_runtime_error(self, provider_with_token, respx_mock):
        import httpx
        respx_mock.post("https://api-inference.huggingface.co/models/google/flan-t5-base").mock(
            return_value=httpx.Response(503, text="Service Unavailable")
        )
        with pytest.raises(RuntimeError, match="503"):
            await provider_with_token.generate("This should fail")

    async def test_custom_model_in_url(self, respx_mock):
        import httpx

        from app.services.llm_provider import HuggingFaceProvider
        custom_model = "mistralai/Mistral-7B-v0.1"
        provider = HuggingFaceProvider(token="hf-fake", default_model=custom_model)
        respx_mock.post(f"https://api-inference.huggingface.co/models/{custom_model}").mock(
            return_value=httpx.Response(200, json=[{"generated_text": "Custom model output"}])
        )
        text, _, model = await provider.generate("prompt", model=custom_model)
        assert text == "Custom model output"
        assert model == custom_model


# ═══════════════════════════════════════════════════════════════════════════════
# OpenAIProvider
# ═══════════════════════════════════════════════════════════════════════════════

class TestOpenAIProvider:
    @pytest.fixture()
    def provider_no_key(self):
        from app.services.llm_provider import OpenAIProvider
        return OpenAIProvider(api_key=None)

    @pytest.fixture()
    def provider_with_key(self):
        from app.services.llm_provider import OpenAIProvider
        return OpenAIProvider(api_key="sk-fake-openai-key-xyz")

    def _openai_response(self, content: str, total_tokens: int | None = None) -> dict:
        resp = {
            "choices": [{"message": {"content": content}}],
        }
        if total_tokens is not None:
            resp["usage"] = {"total_tokens": total_tokens}
        return resp

    async def test_no_key_falls_back_to_mock(self, provider_no_key):
        text, tokens, model = await provider_no_key.generate("What is the capital of France?")
        assert "Paris" in text
        assert tokens > 0

    async def test_http_200_with_usage_field(self, provider_with_key, respx_mock):
        import httpx
        respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json=self._openai_response("OpenAI response here.", total_tokens=77),
            )
        )
        text, tokens, model = await provider_with_key.generate("Hello OpenAI")
        assert text == "OpenAI response here."
        assert tokens == 77

    async def test_http_200_without_usage_field_estimates_tokens(self, provider_with_key, respx_mock):
        import httpx
        respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json=self._openai_response("Response without usage.", total_tokens=None),
            )
        )
        text, tokens, model = await provider_with_key.generate("Token estimate test")
        assert text == "Response without usage."
        assert tokens > 0  # estimated from word count

    async def test_http_error_raises_runtime_error(self, provider_with_key, respx_mock):
        import httpx
        respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": "invalid key"})
        )
        with pytest.raises(RuntimeError, match="401"):
            await provider_with_key.generate("Auth failure test")

    async def test_custom_base_url_used(self, respx_mock):
        import httpx

        from app.services.llm_provider import OpenAIProvider
        provider = OpenAIProvider(
            api_key="sk-fake",
            base_url="https://openrouter.ai/api/v1",
        )
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json=self._openai_response("OpenRouter response.", total_tokens=20),
            )
        )
        text, tokens, _ = await provider.generate("OpenRouter test")
        assert text == "OpenRouter response."
        assert tokens == 20

    async def test_model_name_returned(self, provider_with_key, respx_mock):
        import httpx
        respx_mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json=self._openai_response("ok", total_tokens=5),
            )
        )
        _, _, model = await provider_with_key.generate("model name test", model="gpt-4o")
        assert model == "gpt-4o"


# ═══════════════════════════════════════════════════════════════════════════════
# LLMService routing
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMServiceRouting:
    @pytest.fixture()
    def service(self):
        from app.services.llm_provider import LLMService
        return LLMService()

    async def test_routes_to_mock_by_default(self, service):
        text, tokens, model, provider = await service.execute_inference(
            "What is the capital of France?", provider_name="mock"
        )
        assert provider == "mock"
        assert "Paris" in text

    async def test_routes_to_mock_for_unknown_provider(self, service):
        _, _, _, provider = await service.execute_inference(
            "test", provider_name="unknown_provider"
        )
        assert provider == "mock"

    async def test_routes_to_mock_when_provider_none(self, service):
        # DEFAULT_LLM_PROVIDER is "mock" in test env
        _, _, _, provider = await service.execute_inference("test", provider_name=None)
        assert provider == "mock"

    async def test_huggingface_routing_no_token_still_returns(self, service):
        # With no HF token it falls back to mock — just verify the route is taken
        # and returns a 4-tuple without crashing
        result = await service.execute_inference("test", provider_name="huggingface")
        assert len(result) == 4
        assert result[3] == "huggingface"

    async def test_openai_routing_no_key_still_returns(self, service):
        result = await service.execute_inference("test", provider_name="openai")
        assert len(result) == 4
        assert result[3] == "openai"

    async def test_returns_four_tuple(self, service):
        result = await service.execute_inference("hello", provider_name="mock")
        text, tokens, model, provider = result
        assert isinstance(text, str)
        assert isinstance(tokens, int)
        assert isinstance(model, str)
        assert isinstance(provider, str)
