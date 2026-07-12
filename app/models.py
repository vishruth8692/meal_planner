from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class DietType(str, Enum):
    veg = "veg"
    egg = "egg"
    non_veg = "non_veg"


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    lunch_dinner = "lunch_dinner"  # eligible for lunch or dinner, never breakfast
    any = "any"


class MenuStatus(str, Enum):
    draft = "draft"
    approved = "approved"


class CuisineRegion(str, Enum):
    north = "north"
    south = "south"
    universal = "universal"  # as a dish tag: fits either region; as a preference: no restriction


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FamilyMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    name: str
    is_kid: bool = False
    diet: DietType = DietType.veg
    high_protein_focus: bool = False
    restrictions: Optional[str] = None  # free text, e.g. "no peanuts, low oil"


class HouseholdSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", unique=True, index=True)
    repeat_gap_days: int = 3  # don't repeat a dish within this many days
    cuisine_preference: CuisineRegion = CuisineRegion.universal


class Dish(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    name: str
    diet: DietType = DietType.veg
    protein_source: Optional[str] = None  # e.g. "paneer", "dal", "chicken", "egg"
    protein_grams: Optional[float] = None  # per serving
    calories: Optional[int] = None  # per serving
    meal_type: MealType = MealType.any
    ingredients: Optional[str] = None  # free text, comma separated
    recipe_url: Optional[str] = None
    active: bool = True
    is_special: bool = False  # elaborate/festive dish, surfaced for the Sunday veg special
    region: CuisineRegion = CuisineRegion.universal
    image_url: Optional[str] = None


class CookedLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    dish_id: int = Field(foreign_key="dish.id")
    cooked_on: date


class OutOfStockIngredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    ingredient_name: str
    flagged_on: date = Field(default_factory=date.today)


class DailyMenu(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    menu_date: date
    breakfast_dish_id: Optional[int] = Field(default=None, foreign_key="dish.id")
    lunch_dish_id: Optional[int] = Field(default=None, foreign_key="dish.id")
    dinner_dish_id: Optional[int] = Field(default=None, foreign_key="dish.id")
    sunday_special_dish_id: Optional[int] = Field(default=None, foreign_key="dish.id")
    status: MenuStatus = MenuStatus.draft
    notes: Optional[str] = None
