"""Keyword-based emoji fallback for dishes without a photo, so cards don't read as bare text."""

_EMOJI_KEYWORDS = [
    ("noodle", "🍜"),
    ("pasta", "🍝"),
    ("sandwich", "🥪"),
    ("omelette", "🍳"),
    ("omlette", "🍳"),
    ("bhurji", "🍳"),
    ("egg", "🍳"),
    ("dosa", "🥞"),
    ("uttapam", "🥞"),
    ("chilla", "🥞"),
    ("idli", "⚪"),
    ("vada", "🍩"),
    ("paratha", "🫓"),
    ("puri", "🫓"),
    ("roti", "🫓"),
    ("chapati", "🫓"),
    ("biryani", "🍛"),
    ("pulao", "🍚"),
    ("curd rice", "🍚"),
    ("rice", "🍚"),
    ("chicken", "🍗"),
    ("fish", "🐟"),
    ("mutton", "🍖"),
    ("paneer", "🧀"),
    ("sambar", "🍲"),
    ("rasam", "🍲"),
    ("dal", "🍲"),
    ("curry", "🍛"),
    ("upma", "🍚"),
    ("poha", "🍚"),
    ("pongal", "🍚"),
    ("oats", "🥣"),
    ("salad", "🥗"),
]
_DEFAULT_EMOJI = "🍽️"


def dish_emoji(dish) -> str:
    haystack = f"{dish.name} {dish.protein_source or ''}".lower()
    for keyword, emoji in _EMOJI_KEYWORDS:
        if keyword in haystack:
            return emoji
    return _DEFAULT_EMOJI
