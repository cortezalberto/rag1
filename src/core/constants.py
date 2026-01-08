from enum import Enum


class DecisionType(str, Enum):
    """RAG response decision types based on confidence levels."""

    ANSWER = "answer"
    SOFT_DISCLAIMER = "soft_disclaimer"
    DISCLAIMER = "disclaimer"


# Allergy-related trigger words for conservative mode
ALLERGY_TRIGGERS: tuple[str, ...] = (
    "alerg",
    "celiac",
    "sin tacc",
    "gluten",
    "lactosa",
    "lácteo",
    "lacteos",
    "lácteos",
    "mani",
    "maní",
    "huevo",
    "soja",
    "pescado",
    "marisco",
    "sesamo",
    "sésamo",
    "intoler",
    "trazas",
    "contiene",
    "puede contener",
)
