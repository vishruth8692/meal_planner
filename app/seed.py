from sqlmodel import Session

from app.models import CuisineRegion, Dish, DietType, MealType

N = CuisineRegion.north
S = CuisineRegion.south
U = CuisineRegion.universal

# name, diet, protein_source, meal_type, ingredients, protein_grams, calories, is_special, region
STARTER_DISHES = [
    # -- lunch / dinner mains --
    ("Dal tadka", DietType.veg, "dal", MealType.lunch_dinner, "toor dal, tomato, onion, garlic", 9, 180, False, U),
    ("Rajma", DietType.veg, "rajma", MealType.lunch, "rajma, onion, tomato", 8, 210, False, N),
    ("Chole", DietType.veg, "chana", MealType.lunch, "chickpeas, onion, tomato", 8, 220, False, N),
    ("Paneer butter masala", DietType.veg, "paneer", MealType.dinner, "paneer, tomato, cream, butter", 14, 320, True, N),
    ("Palak paneer", DietType.veg, "paneer", MealType.dinner, "spinach, paneer", 13, 280, False, N),
    ("Bhindi fry", DietType.veg, "vegetable", MealType.lunch_dinner, "okra, onion", 3, 120, False, U),
    ("Aloo gobi", DietType.veg, "vegetable", MealType.lunch_dinner, "potato, cauliflower", 4, 150, False, U),
    ("Mixed veg curry", DietType.veg, "vegetable", MealType.lunch_dinner, "carrot, beans, peas, potato", 5, 160, False, U),
    ("Baingan bharta", DietType.veg, "vegetable", MealType.dinner, "brinjal, onion, tomato", 3, 140, False, N),
    ("Cabbage poriyal", DietType.veg, "vegetable", MealType.lunch_dinner, "cabbage, coconut, mustard seeds", 3, 110, False, S),
    ("Curd rice", DietType.veg, "dairy", MealType.lunch, "rice, curd", 6, 200, False, S),
    ("Sambar", DietType.veg, "dal", MealType.lunch, "toor dal, drumstick, tamarind", 7, 150, False, S),
    ("Rasam", DietType.veg, "dal", MealType.lunch, "tamarind, tomato, dal", 3, 80, False, S),
    ("Egg curry", DietType.egg, "egg", MealType.dinner, "egg, onion, tomato", 12, 220, False, U),
    ("Chicken curry", DietType.non_veg, "chicken", MealType.dinner, "chicken, onion, tomato", 25, 320, False, U),
    ("Chicken fry", DietType.non_veg, "chicken", MealType.dinner, "chicken, spices", 27, 300, False, U),
    ("Fish curry", DietType.non_veg, "fish", MealType.dinner, "fish, coconut, tamarind", 22, 260, False, S),
    ("Mutton curry", DietType.non_veg, "mutton", MealType.dinner, "mutton, onion, spices", 24, 350, False, U),
    ("Vegetable pulao", DietType.veg, "rice", MealType.lunch, "rice, mixed vegetables", 6, 280, True, U),
    ("Roti + bhindi fry", DietType.veg, "vegetable", MealType.dinner, "wheat flour, okra, onion", 6, 260, False, N),
    ("Roti + aloo gobi", DietType.veg, "vegetable", MealType.dinner, "wheat flour, potato, cauliflower", 6, 280, False, N),
    ("Roti + palak paneer", DietType.veg, "paneer", MealType.dinner, "wheat flour, spinach, paneer", 15, 380, True, N),
    ("Veg noodles", DietType.veg, "vegetable", MealType.lunch_dinner, "noodles, cabbage, carrot, capsicum, soy sauce", 6, 320, False, U),
    ("Veg pasta", DietType.veg, "vegetable", MealType.lunch_dinner, "pasta, tomato, cheese, mixed vegetables", 9, 340, False, U),

    # -- breakfast: exhaustive list, north + south + universal --
    ("Egg bhurji", DietType.egg, "egg", MealType.breakfast, "egg, onion, tomato", 11, 180, False, U),
    ("Bread omelette", DietType.egg, "egg", MealType.breakfast, "bread, egg, onion", 13, 260, False, U),
    ("Poha", DietType.veg, "vegetable", MealType.breakfast, "flattened rice, onion, peanut", 4, 250, False, U),
    ("Upma", DietType.veg, "vegetable", MealType.breakfast, "semolina, vegetables", 5, 220, False, S),
    ("Semiya upma", DietType.veg, "vegetable", MealType.breakfast, "vermicelli, vegetables, mustard seeds", 5, 210, False, S),
    ("Dosa + chutney", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, coconut", 6, 210, False, S),
    ("Idli + sambar", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, toor dal", 7, 190, False, S),
    ("Uttapam", DietType.veg, "lentil", MealType.breakfast, "rice, urad dal, onion, tomato", 6, 230, False, S),
    ("Rava idli", DietType.veg, "vegetable", MealType.breakfast, "semolina, curd, mustard seeds", 5, 180, False, S),
    ("Pongal", DietType.veg, "lentil", MealType.breakfast, "rice, moong dal, pepper, ghee", 7, 240, False, S),
    ("Medu vada", DietType.veg, "lentil", MealType.breakfast, "urad dal, onion, curry leaves", 6, 200, False, S),
    ("Paratha + curd", DietType.veg, "dairy", MealType.breakfast, "wheat flour, ghee, curd", 6, 280, False, N),
    ("Aloo paratha", DietType.veg, "vegetable", MealType.breakfast, "wheat flour, potato, ghee", 7, 320, False, N),
    ("Puri bhaji", DietType.veg, "vegetable", MealType.breakfast, "wheat flour, potato, oil", 6, 300, False, N),
    ("Moong dal chilla", DietType.veg, "lentil", MealType.breakfast, "moong dal, onion, tomato", 9, 180, False, U),
    ("Besan chilla", DietType.veg, "lentil", MealType.breakfast, "besan, onion, tomato", 8, 190, False, U),
    ("Sandwich", DietType.veg, "vegetable", MealType.breakfast, "bread, cucumber, tomato, cheese", 8, 230, False, U),
    ("Oats porridge", DietType.veg, "vegetable", MealType.breakfast, "oats, milk", 8, 210, False, U),
]


def seed_starter_dishes(session: Session, owner_id: int) -> None:
    for name, diet, protein, meal, ingredients, protein_grams, calories, is_special, region in STARTER_DISHES:
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
                region=region,
            )
        )
    session.commit()
