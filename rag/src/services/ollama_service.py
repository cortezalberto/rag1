import httpx

from src.config import Settings
from src.core.exceptions import OllamaError, OllamaConnectionError, OllamaTimeoutError


class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._base_url = settings.ollama_url

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using Ollama."""
        try:
            async with httpx.AsyncClient(timeout=self._settings.ollama_embed_timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._settings.embed_model, "prompt": text},
                )

                if response.status_code != 200:
                    raise OllamaError(
                        message="Ollama embeddings error",
                        detail=response.text,
                    )

                data = response.json()
                embedding = data.get("embedding")

                if not embedding:
                    raise OllamaError(
                        message="Ollama embeddings: missing 'embedding' in response",
                    )

                return embedding

        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                message="Cannot connect to Ollama",
                detail=str(e),
            )
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                message="Ollama embedding request timed out",
                detail=str(e),
            )

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Generate chat response using Ollama."""
        payload = {
            "model": self._settings.chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self._settings.ollama_chat_timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )

                if response.status_code != 200:
                    raise OllamaError(
                        message="Ollama chat error",
                        detail=response.text,
                    )

                data = response.json()
                content = data.get("message", {}).get("content", "") or ""
                return content.strip()

        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                message="Cannot connect to Ollama",
                detail=str(e),
            )
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                message="Ollama chat request timed out",
                detail=str(e),
            )

    async def is_reachable(self) -> bool:
        """Check if Ollama service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self._settings.ollama_health_timeout) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
