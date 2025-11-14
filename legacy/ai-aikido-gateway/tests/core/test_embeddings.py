"""Tests for embedding providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.embeddings import OpenAIEmbeddingProvider
from src.core.embeddings.base import EmbeddingResult


class TestOpenAIEmbeddingProvider:
    """Tests for OpenAI embedding provider."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch("src.core.embeddings.openai.openai.AsyncOpenAI") as mock:
            client = MagicMock()
            mock.return_value = client

            # Mock embeddings.create response
            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(embedding=[0.1] * 1536)
            ]
            mock_usage = MagicMock()
            mock_usage.total_tokens = 10
            mock_response.usage = mock_usage
            client.embeddings.create = AsyncMock(return_value=mock_response)

            yield client

    @pytest.fixture
    def provider(self, mock_openai_client):
        """Create provider instance."""
        return OpenAIEmbeddingProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_embed_single_text(self, provider, mock_openai_client):
        """Test embedding a single text."""
        text = "Hello, world!"

        result = await provider.embed(text)

        assert isinstance(result, EmbeddingResult)
        assert isinstance(result.vector, list)
        assert len(result.vector) == 1536
        assert result.prompt_tokens == 10

        # Verify API was called correctly
        mock_openai_client.embeddings.create.assert_called_once()
        call_args = mock_openai_client.embeddings.create.call_args
        assert call_args[1]["model"] == "text-embedding-ada-002"
        assert call_args[1]["input"] == text

    @pytest.mark.asyncio
    async def test_embed_empty_text(self, provider):
        """Test embedding empty text returns zero vector."""
        result = await provider.embed("")

        assert isinstance(result.vector, list)
        assert len(result.vector) == 1536
        assert all(x == 0.0 for x in result.vector)

    @pytest.mark.asyncio
    async def test_embed_batch(self, provider, mock_openai_client):
        """Test batch embedding."""
        # Update mock for batch response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
            MagicMock(embedding=[0.3] * 1536),
        ]
        mock_openai_client.embeddings.create.return_value = mock_response

        texts = ["Hello", "World", "Test"]
        results = await provider.embed_batch(texts)

        assert len(results) == 3
        assert all(len(res.vector) == 1536 for res in results)

    @pytest.mark.asyncio
    async def test_embed_batch_with_empty_texts(self, provider, mock_openai_client):
        """Test batch embedding with some empty texts."""
        # Update mock for batch response (only 2 non-empty texts)
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
        ]
        mock_openai_client.embeddings.create.return_value = mock_response

        texts = ["Hello", "", "World"]
        results = await provider.embed_batch(texts)

        assert len(results) == 3
        assert all(x == 0.0 for x in results[1].vector)  # Empty text gets zero vector

    def test_dimension_property(self, provider):
        """Test dimension property."""
        assert provider.dimension == 1536

    def test_model_name_property(self, provider):
        """Test model name property."""
        assert provider.model_name == "text-embedding-ada-002"

    def test_custom_model(self):
        """Test provider with custom model."""
        with patch("src.core.embeddings.openai.openai.AsyncOpenAI"):
            provider = OpenAIEmbeddingProvider(
                api_key="test-key",
                model="text-embedding-3-large"
            )

            assert provider.model_name == "text-embedding-3-large"
            assert provider.dimension == 3072

    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(ValueError, match="API key is required"):
            OpenAIEmbeddingProvider(api_key="")

    @pytest.mark.asyncio
    async def test_retry_on_api_error(self, provider, mock_openai_client):
        """Test retry logic on API errors."""
        import openai
        from unittest.mock import Mock

        # First two calls fail, third succeeds
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        # Create mock request object for OpenAI APIError
        mock_request = Mock()
        mock_request.url = "https://api.openai.com/v1/embeddings"

        mock_openai_client.embeddings.create.side_effect = [
            openai.APIError("API Error", request=mock_request, body=None),
            openai.APIError("API Error", request=mock_request, body=None),
            mock_response
        ]

        result = await provider.embed("Test")

        assert len(result.vector) == 1536
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, provider, mock_openai_client):
        """Test that max retries are respected."""
        import openai
        from unittest.mock import Mock

        # Create mock request object for OpenAI APIError
        mock_request = Mock()
        mock_request.url = "https://api.openai.com/v1/embeddings"

        # All calls fail
        mock_openai_client.embeddings.create.side_effect = openai.APIError("API Error", request=mock_request, body=None)

        with pytest.raises(openai.APIError):
            await provider.embed("Test")

        assert mock_openai_client.embeddings.create.call_count == 3  # max_retries
