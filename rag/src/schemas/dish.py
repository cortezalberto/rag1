from pydantic import BaseModel


class DishOut(BaseModel):
    """Response schema for dish information."""

    id: int
    name: str
    category: str
    price_cents: int
    tags: list[str]

    model_config = {"from_attributes": True}
