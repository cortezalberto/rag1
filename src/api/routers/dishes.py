from fastapi import APIRouter

from src.schemas import DishOut
from src.api.dependencies import DishRepoDep


router = APIRouter(tags=["dishes"])


@router.get("/dishes", response_model=list[DishOut])
def list_dishes(dish_repo: DishRepoDep) -> list[DishOut]:
    """List all active dishes."""
    dishes = dish_repo.get_all_active()
    return [
        DishOut(
            id=d.id,
            name=d.name,
            category=d.category,
            price_cents=d.price_cents,
            tags=d.tags or [],
        )
        for d in dishes
    ]
