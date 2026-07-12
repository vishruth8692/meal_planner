import random
from datetime import date, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import (
    CookedLog,
    CuisineRegion,
    Dish,
    DietType,
    HouseholdSettings,
    MealType,
    OutOfStockIngredient,
)

DIET_RANK = {DietType.veg: 0, DietType.egg: 1, DietType.non_veg: 2}

OUT_OF_STOCK_EXPIRY_DAYS = 7


def _get_settings(session: Session, owner_id: int) -> HouseholdSettings:
    settings = session.exec(select(HouseholdSettings).where(HouseholdSettings.owner_id == owner_id)).first()
    if settings is None:
        settings = HouseholdSettings(owner_id=owner_id)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def _last_cooked_dates(session: Session, owner_id: int) -> dict[int, date]:
    logs = session.exec(select(CookedLog).where(CookedLog.owner_id == owner_id)).all()
    last_cooked: dict[int, date] = {}
    for log in logs:
        if log.dish_id not in last_cooked or log.cooked_on > last_cooked[log.dish_id]:
            last_cooked[log.dish_id] = log.cooked_on
    return last_cooked


def _purge_expired_out_of_stock(session: Session, owner_id: int) -> None:
    cutoff = date.today() - timedelta(days=OUT_OF_STOCK_EXPIRY_DAYS)
    expired = session.exec(
        select(OutOfStockIngredient).where(
            OutOfStockIngredient.owner_id == owner_id, OutOfStockIngredient.flagged_on <= cutoff
        )
    ).all()
    if not expired:
        return
    for item in expired:
        session.delete(item)
    session.commit()


def _out_of_stock_names(session: Session, owner_id: int) -> set[str]:
    _purge_expired_out_of_stock(session, owner_id)
    items = session.exec(select(OutOfStockIngredient).where(OutOfStockIngredient.owner_id == owner_id)).all()
    return {o.ingredient_name.strip().lower() for o in items}


def get_out_of_stock_names(session: Session, owner_id: int) -> set[str]:
    """Public entry point for callers (e.g. the dashboard) that just need the current out-of-stock set."""
    return _out_of_stock_names(session, owner_id)


def _has_out_of_stock_ingredient(dish: Dish, out_of_stock: set[str]) -> bool:
    if not dish.ingredients or not out_of_stock:
        return False
    dish_ingredients = {i.strip().lower() for i in dish.ingredients.split(",")}
    return bool(dish_ingredients & out_of_stock)


def _fits_meal(dish_meal_type: MealType, meal_type: MealType) -> bool:
    if dish_meal_type == meal_type or dish_meal_type == MealType.any:
        return True
    if dish_meal_type == MealType.lunch_dinner:
        return meal_type in (MealType.lunch, MealType.dinner)
    return False


def _fits_region(dish_region: CuisineRegion, preference: CuisineRegion) -> bool:
    if preference == CuisineRegion.universal or dish_region == CuisineRegion.universal:
        return True
    return dish_region == preference


def _fits_diet(dish_diet: DietType, household_diet: DietType) -> bool:
    return DIET_RANK[dish_diet] <= DIET_RANK[household_diet]


def _eligible_dishes(
    session: Session,
    owner_id: int,
    meal_type: MealType,
    settings: HouseholdSettings,
    last_cooked: dict[int, date],
    out_of_stock: set[str],
    exclude_ids: set[int],
    today: date,
) -> list[Dish]:
    dishes = session.exec(
        select(Dish).where(Dish.owner_id == owner_id, Dish.active == True)  # noqa: E712
    ).all()
    eligible = []
    for dish in dishes:
        if dish.id in exclude_ids:
            continue
        if not _fits_meal(dish.meal_type, meal_type):
            continue
        if not _fits_region(dish.region, settings.cuisine_preference):
            continue
        if not _fits_diet(dish.diet, settings.household_diet):
            continue
        if _has_out_of_stock_ingredient(dish, out_of_stock):
            continue
        last = last_cooked.get(dish.id)
        if last and (today - last).days < settings.repeat_gap_days:
            continue
        eligible.append(dish)
    return eligible


def get_candidates(
    session: Session,
    owner_id: int,
    meal_type: MealType,
    count: int = 3,
    exclude_dish_ids: Optional[set[int]] = None,
    target_date: Optional[date] = None,
) -> list[Dish]:
    """Return up to `count` suggested dishes for a meal slot, for the user to pick from."""
    today = target_date or date.today()
    settings = _get_settings(session, owner_id)
    last_cooked = _last_cooked_dates(session, owner_id)
    out_of_stock = _out_of_stock_names(session, owner_id)

    eligible = _eligible_dishes(
        session, owner_id, meal_type, settings, last_cooked, out_of_stock, exclude_dish_ids or set(), today
    )
    eligible.sort(key=lambda d: last_cooked.get(d.id, date.min))
    pool = eligible[: max(count * 2, count)]

    rnd = random.Random(f"{owner_id}-{today.isoformat()}-{meal_type.value}-{len(eligible)}")
    rnd.shuffle(pool)
    candidates = pool[:count]

    # Sunday treat: guarantee a non-veg option shows up for households that eat non-veg
    allow_non_veg = settings.household_diet == DietType.non_veg
    if today.weekday() == 6 and allow_non_veg and meal_type in (MealType.lunch, MealType.dinner):
        candidates = _ensure_nonveg_present(candidates, eligible, count)
    return candidates


def _ensure_nonveg_present(candidates: list[Dish], eligible: list[Dish], count: int) -> list[Dish]:
    if any(d.diet == DietType.non_veg for d in candidates):
        return candidates
    nonveg_options = [d for d in eligible if d.diet == DietType.non_veg and d not in candidates]
    if not nonveg_options:
        return candidates
    replacement = nonveg_options[0]
    if len(candidates) >= count:
        return candidates[:-1] + [replacement]
    return candidates + [replacement]


def get_special_candidates(
    session: Session,
    owner_id: int,
    count: int = 3,
    exclude_dish_ids: Optional[set[int]] = None,
    target_date: Optional[date] = None,
) -> list[Dish]:
    """Sunday-only veg special candidates — elaborate dishes marked `is_special`."""
    today = target_date or date.today()
    settings = _get_settings(session, owner_id)
    last_cooked = _last_cooked_dates(session, owner_id)
    out_of_stock = _out_of_stock_names(session, owner_id)
    exclude = exclude_dish_ids or set()

    dishes = session.exec(
        select(Dish).where(Dish.owner_id == owner_id, Dish.active == True, Dish.is_special == True)  # noqa: E712
    ).all()
    eligible = []
    for dish in dishes:
        if dish.id in exclude or dish.diet == DietType.non_veg:
            continue
        if not _fits_region(dish.region, settings.cuisine_preference):
            continue
        if _has_out_of_stock_ingredient(dish, out_of_stock):
            continue
        last = last_cooked.get(dish.id)
        if last and (today - last).days < settings.repeat_gap_days:
            continue
        eligible.append(dish)

    eligible.sort(key=lambda d: last_cooked.get(d.id, date.min))
    pool = eligible[: max(count * 2, count)]
    rnd = random.Random(f"{owner_id}-{today.isoformat()}-special-{len(eligible)}")
    rnd.shuffle(pool)
    return pool[:count]


WEEK_MEALS = (MealType.breakfast, MealType.lunch, MealType.dinner)


def plan_week(
    session: Session, owner_id: int, start_date: Optional[date] = None, days: int = 7
) -> list[tuple[date, dict[str, Optional[Dish]]]]:
    """Suggest a dish per meal for each of the next `days` days, avoiding repeats within the week.

    This is a forward-looking suggestion for shopping/planning purposes — it isn't persisted,
    so it doesn't lock in what will actually be cooked (that's decided day-by-day on the dashboard).
    """
    start = start_date or date.today()
    used_this_week: dict[MealType, set[int]] = {meal: set() for meal in WEEK_MEALS}
    plan = []
    for i in range(days):
        day = start + timedelta(days=i)
        day_plan: dict[str, Optional[Dish]] = {}
        used_today: set[int] = set()
        for meal in WEEK_MEALS:
            exclude = used_this_week[meal] | used_today
            candidates = get_candidates(session, owner_id, meal, count=1, exclude_dish_ids=exclude, target_date=day)
            dish = candidates[0] if candidates else None
            if dish:
                used_this_week[meal].add(dish.id)
                used_today.add(dish.id)
            day_plan[meal.value] = dish
        plan.append((day, day_plan))
    return plan
