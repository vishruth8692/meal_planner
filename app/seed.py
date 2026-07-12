from sqlmodel import Session

from app.models import Dish, DietType, MealType

# name, diet, protein_source, meal_type, ingredients, protein_grams, calories, is_special
STARTER_DISHES = [
    ("Dal tadka", DietType.veg, "dal", MealType.lunch_dinner, "toor dal, tomato, onion, garlic", 9, 180, False),
    ("Rajma", DietType.veg, "rajma", MealType.lunch, "rajma, onion, tomato", 8, 210, False),
    ("Chole", DietType.veg, "chana", MealType.lunch, "chickpeas, onion, tomato", 8, 220, False),
    ("Paneer butter masala", DietType.veg, "paneer", MealType.dinner, "paneer, tomato, cream, butter", 14, 320, True),
    ("Palak paneer", DietType.veg, "paneer", MealType.dinner, "spinach, paneer", 13, 280, False),
    ("Bhindi fry", DietType.veg, "vegetable", MealType.lunch_dinner, "okra, onion", 3, 120, False),
    ("Aloo gobi", DietType.veg, "vegetable", MealType.lunch_dinner, "potato, cauliflower", 4, 150, False),
    ("Mixed veg curry", DietType.veg, "vegetable", MealType.lunch_dinner, "carrot, beans, peas, potato", 5, 160, False),
    ("Baingan bharta", DietType.veg, "vegetable", MealType.dinner, "brinjal, onion, tomato", 3, 140, False),
    ("Cabbage poriyal", DietType.veg, "vegetable", MealType.lunch_dinner, "cabbage, coconut, mustard seeds", 3, 110, False),
    ("Curd rice", DietType.veg, "dairy", MealType.lunch, "rice, curd", 6, 200, False),
    ("Sambar", DietType.veg, "dal", MealType.lunch, "toor dal, drumstick, tamarind", 7, 150, False),
    ("Rasam", DietType.veg, "dal", MealType.lunch, "tamarind, tomato, dal", 3, 80, False),
    ("Egg curry", DietType.egg, "egg", MealType.dinner, "egg, onion, tomato", 12, 220, False),
    ("Egg bhurji", DietType.egg, "egg", MealType.breakfast, "egg, onion, tomato", 11, 180, False),
    ("Chicken curry", DietType.non_veg, "chicken", MealType.dinner, "chicken, onion, tomato", 25, 320, False),
    ("Chicken fry", DietType.non_veg, "chicken", MealType.dinner, "chicken, spices", 27, 300, False),
    ("Fish curry", DietType.non_veg, "fish", MealType.dinner, "fish, coconut, tamarind", 22, 260, False),
    ("Mutton curry", DietType.non_veg, "mutton", MealType.dinner, "mutton, onion, spices", 24, 350, False),
    ("Vegetable pulao", DietType.veg, "rice", MealType.lunch, "rice, mixed vegetables", 6, 280, True),
    ("Poha", DietType.veg, "vegetable", MealType.breakfast, "flattened rice, onion, peanut", 4, 250, False),
    ("Upma", DietType.veg, "vegetable", MealType.breakfast, "semolina, vegetables", 5, 220, False),
    ("Dosa + chutney", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, coconut", 6, 210, False),
    ("Idli + sambar", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, toor dal", 7, 190, False),
    ("Roti + bhindi fry", DietType.veg, "vegetable", MealType.dinner, "wheat flour, okra, onion", 6, 260, False),
    ("Roti + aloo gobi", DietType.veg, "vegetable", MealType.dinner, "wheat flour, potato, cauliflower", 6, 280, False),
    ("Roti + palak paneer", DietType.veg, "paneer", MealType.dinner, "wheat flour, spinach, paneer", 15, 380, True),
]


def seed_starter_dishes(session: Session, owner_id: int) -> None:
    for name, diet, protein, meal, ingredients, protein_grams, calories, is_special in STARTER_DISHES:
        session.add(
            Dish(
                owner_id=owner_id,
                name=name,
                diet=diet,
                protein_source=protein,
                meal_type=meal,
                ingredients=ingredients,
                protein_grams=protein_grams,
                calories=calories,
                is_special=is_special,
            )
        )
    session.commit()
