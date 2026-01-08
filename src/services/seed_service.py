from src.config import Settings
from src.repositories import DishRepository, ChunkRepository
from src.models.entities import Dish
from .text_service import TextService
from data.seed_dishes import build_seed_dishes


class SeedService:
    """Service for seeding initial data."""

    def __init__(
        self,
        dish_repo: DishRepository,
        chunk_repo: ChunkRepository,
        text_service: TextService,
        settings: Settings,
    ):
        self._dish_repo = dish_repo
        self._chunk_repo = chunk_repo
        self._text_service = text_service
        self._settings = settings

    def seed_dishes(self) -> tuple[bool, str]:
        """
        Seed the database with initial dishes.

        Returns:
            Tuple of (success, message)
        """
        # Check if data already exists
        existing_count = self._dish_repo.count()
        if existing_count > 0:
            return True, "Ya hay datos. Si querés reiniciar, borrá tablas o limpiá manualmente."

        # Get seed data
        dishes_data = build_seed_dishes()

        # Create dishes and chunks
        for dish_data in dishes_data:
            # Create dish
            dish = Dish(
                name=dish_data["name"],
                category=dish_data["category"],
                price_cents=dish_data["price_cents"],
                tags=dish_data["tags"],
                is_active=True,
            )
            self._dish_repo.create(dish)

            # Create chunks from ficha text
            ficha_text = dish_data["ficha_text"]
            chunks_content = self._text_service.chunk(ficha_text)
            self._chunk_repo.create_for_dish(
                dish_id=dish.id,
                chunks_content=chunks_content,
            )

        self._dish_repo.commit()
        return True, "Seed OK: 10 platos + fichas cargadas."
