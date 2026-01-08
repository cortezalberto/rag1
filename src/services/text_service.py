import re

from src.config import Settings
from src.core.constants import ALLERGY_TRIGGERS


class TextService:
    """Service for text processing operations."""

    def __init__(self, settings: Settings):
        self._settings = settings

    def normalize(self, text: str) -> str:
        """Normalize text by cleaning whitespace."""
        text = text.replace("\u00a0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def chunk(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        text = self.normalize(text)
        if not text:
            return []

        chunk_size = self._settings.chunk_size
        overlap = self._settings.chunk_overlap
        step = max(1, chunk_size - overlap)

        chunks = []
        i = 0
        while i < len(text):
            part = text[i : i + chunk_size].strip()
            if part:
                chunks.append(part)
            i += step

        return chunks

    def is_allergy_query(self, query: str) -> bool:
        """Check if query is about allergies or dietary restrictions."""
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in ALLERGY_TRIGGERS)

    def truncate_for_preview(self, text: str) -> str:
        """Truncate text for preview display."""
        normalized = self.normalize(text)
        max_chars = self._settings.source_preview_chars
        truncated = normalized[:max_chars].replace("\n", " ")
        return truncated
