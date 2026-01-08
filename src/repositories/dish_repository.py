from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.entities import Dish


class DishRepository:
    """Repository for Dish entity operations."""

    def __init__(self, db: Session):
        self._db = db

    def get_all_active(self) -> list[Dish]:
        """Get all active dishes ordered by id."""
        stmt = select(Dish).where(Dish.is_active == True).order_by(Dish.id)
        return list(self._db.execute(stmt).scalars().all())

    def get_by_id(self, dish_id: int) -> Dish | None:
        """Get a dish by its ID."""
        return self._db.get(Dish, dish_id)

    def count(self) -> int:
        """Count total dishes."""
        return self._db.scalar(select(func.count()).select_from(Dish)) or 0

    def create(self, dish: Dish) -> Dish:
        """Create a new dish."""
        self._db.add(dish)
        self._db.flush()
        return dish

    def create_many(self, dishes: list[Dish]) -> list[Dish]:
        """Create multiple dishes."""
        for dish in dishes:
            self._db.add(dish)
        self._db.flush()
        return dishes

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()
