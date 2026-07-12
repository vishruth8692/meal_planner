from sqlmodel import Session

from app.models import Dish, DietType, MealType

# name, diet, protein_source, meal_type, ingredients, protein_grams, calories (per serving, approx)
STARTER_DISHES = [
    ("Dal tadka", DietType.veg, "dal", MealType.lunch_dinner, "toor dal, tomato, onion, garlic", 9, 180),
    ("Rajma", DietType.veg, "rajma", MealType.lunch, "rajma, onion, tomato", 8, 210),
    ("Chole", DietType.veg, "chana", MealType.lunch, "chickpeas, onion, tomato", 8, 220),
    ("Paneer butter masala", DietType.veg, "paneer", MealType.dinner, "paneer, tomato, cream, butter", 14, 320),
    ("Palak paneer", DietType.veg, "paneer", MealType.dinner, "spinach, paneer", 13, 280),
    ("Bhindi fry", DietType.veg, "vegetable", MealType.lunch_dinner, "okra, onion", 3, 120),
    ("Aloo gobi", DietType.veg, "vegetable", MealType.lunch_dinner, "potato, cauliflower", 4, 150),
    ("Mixed veg curry", DietType.veg, "vegetable", MealType.lunch_dinner, "carrot, beans, peas, potato", 5, 160),
    ("Baingan bharta", DietType.veg, "vegetable", MealType.dinner, "brinjal, onion, tomato", 3, 140),
    ("Cabbage poriyal", DietType.veg, "vegetable", MealType.lunch_dinner, "cabbage, coconut, mustard seeds", 3, 110),
    ("Curd rice", DietType.veg, "dairy", MealType.lunch, "rice, curd", 6, 200),
    ("Sambar", DietType.veg, "dal", MealType.lunch, "toor dal, drumstick, tamarind", 7, 150),
    ("Rasam", DietType.veg, "dal", MealType.lunch, "tamarind, tomato, dal", 3, 80),
    ("Egg curry", DietType.egg, "egg", MealType.dinner, "egg, onion, tomato", 12, 220),
    ("Egg bhurji", DietType.egg, "egg", MealType.breakfast, "egg, onion, tomato", 11, 180),
    ("Chicken curry", DietType.non_veg, "chicken", MealType.dinner, "chicken, onion, tomato", 25, 320),
    ("Chicken fry", DietType.non_veg, "chicken", MealType.dinner, "chicken, spices", 27, 300),
    ("Fish curry", DietType.non_veg, "fish", MealType.dinner, "fish, coconut, tamarind", 22, 260),
    ("Mutton curry", DietType.non_veg, "mutton", MealType.dinner, "mutton, onion, spices", 24, 350),
    ("Vegetable pulao", DietType.veg, "rice", MealType.lunch, "rice, mixed vegetables", 6, 280),
    ("Poha", DietType.veg, "vegetable", MealType.breakfast, "flattened rice, onion, peanut", 4, 250),
    ("Upma", DietType.veg, "vegetable", MealType.breakfast, "semolina, vegetables", 5, 220),
    ("Dosa + chutney", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, coconut", 6, 210),
    ("Idli + sambar", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, toor dal", 7, 190),
    ("Roti + bhindi fry", DietType.veg, "vegetable", MealType.dinner, "wheat flour, okra, onion", 6, 260),
    ("Roti + aloo gobi", DietType.veg, "vegetable", MealType.dinner, "wheat flour, potato, cauliflower", 6, 280),
    ("Roti + palak paneer", DietType.veg, "paneer", MealType.dinner, "wheat flour, spinach, paneer", 15, 380),
]


def seed_starter_dishes(session: Session, owner_id: int) -> None:
    for name, diet, protein, meal, ingredients, protein_grams, calories in STARTER_DISHES:
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
            )
        )
    session.commit()
