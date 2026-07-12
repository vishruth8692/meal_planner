import os
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from starlette.middleware.sessions import SessionMiddleware

from app.auth import hash_password, verify_password
from app.database import get_session, init_db
from app.models import (
    CookedLog,
    CuisineRegion,
    DailyMenu,
    Dish,
    DietType,
    FamilyMember,
    HouseholdSettings,
    MealType,
    MenuStatus,
    OutOfStockIngredient,
    User,
)
from app.seed import seed_starter_dishes
from app.suggest import OUT_OF_STOCK_EXPIRY_DAYS, get_candidates, get_special_candidates, plan_week
from app.visuals import dish_emoji

app = FastAPI(title="CookHelper")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev-only-insecure-secret"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["dish_emoji"] = dish_emoji


@app.on_event("startup")
def on_startup():
    init_db()


def _current_user(request: Request, session: Session) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return session.get(User, user_id)


def render(request: Request, user: Optional[User], template: str, context: dict):
    context = {**context, "request": request, "current_user": user}
    return templates.TemplateResponse(template, context)


# ---------- auth ----------


@app.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "current_user": None, "error": None})


@app.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    cuisine_preference: str = Form("universal"),
    session: Session = Depends(get_session),
):
    username = username.strip().lower()
    if len(username) < 3 or len(password) < 6:
        return render(
            request, None, "signup.html", {"error": "Username must be 3+ characters, password 6+ characters."}
        )
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        return render(request, None, "signup.html", {"error": "That username is already taken."})

    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    seed_starter_dishes(session, user.id)
    session.add(HouseholdSettings(owner_id=user.id, cuisine_preference=CuisineRegion(cuisine_preference)))
    session.commit()

    request.session["user_id"] = user.id
    return RedirectResponse("/profile", status_code=303)


@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None, "error": None})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    username = username.strip().lower()
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.password_hash):
        return render(request, None, "login.html", {"error": "Invalid username or password."})
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ---------- dashboard ----------


def _get_or_create_menu(session: Session, owner_id: int, target_date: date) -> DailyMenu:
    menu = session.exec(
        select(DailyMenu).where(DailyMenu.owner_id == owner_id, DailyMenu.menu_date == target_date)
    ).first()
    if menu is None:
        menu = DailyMenu(owner_id=owner_id, menu_date=target_date)
        session.add(menu)
        session.commit()
        session.refresh(menu)
    return menu


def _whatsapp_text(
    menu: DailyMenu, breakfast: Optional[Dish], lunch: Dish, dinner: Dish, sunday_special: Optional[Dish]
) -> str:
    lines = [f"Menu for {menu.menu_date.strftime('%d %b')}:"]
    if breakfast:
        lines.append(f"Breakfast: {breakfast.name}" + (f" ({breakfast.recipe_url})" if breakfast.recipe_url else ""))
    lines.append(f"Lunch: {lunch.name}" + (f" ({lunch.recipe_url})" if lunch.recipe_url else ""))
    lines.append(f"Dinner: {dinner.name}" + (f" ({dinner.recipe_url})" if dinner.recipe_url else ""))
    if sunday_special:
        lines.append(
            f"Sunday Special: {sunday_special.name}"
            + (f" ({sunday_special.recipe_url})" if sunday_special.recipe_url else "")
        )
    if menu.notes:
        lines.append(f"Note: {menu.notes}")
    return "\n".join(lines)


def _candidates_with_selection(
    session: Session,
    owner_id: int,
    meal_type: MealType,
    chosen: Optional[Dish],
    exclude_dish_ids: set[int],
    today: date,
) -> list[Dish]:
    """Candidate list for a meal slot, guaranteed to include the currently chosen dish (if any) so it's
    always visible and highlighted rather than hidden once picked."""
    candidates = get_candidates(
        session, owner_id, meal_type, count=3, exclude_dish_ids=exclude_dish_ids, target_date=today
    )
    if chosen and chosen.id not in {c.id for c in candidates}:
        candidates = [chosen] + candidates
    return candidates


@app.get("/")
def dashboard(request: Request, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not session.exec(select(FamilyMember).where(FamilyMember.owner_id == user.id)).first():
        return RedirectResponse("/profile", status_code=303)

    today = date.today()
    menu = _get_or_create_menu(session, user.id, today)

    breakfast = session.get(Dish, menu.breakfast_dish_id) if menu.breakfast_dish_id else None
    lunch = session.get(Dish, menu.lunch_dish_id) if menu.lunch_dish_id else None
    dinner = session.get(Dish, menu.dinner_dish_id) if menu.dinner_dish_id else None

    breakfast_candidates = _candidates_with_selection(session, user.id, MealType.breakfast, breakfast, set(), today)
    lunch_candidates = _candidates_with_selection(session, user.id, MealType.lunch, lunch, set(), today)
    exclude_for_dinner = {lunch.id} if lunch else set()
    dinner_candidates = _candidates_with_selection(
        session, user.id, MealType.dinner, dinner, exclude_for_dinner, today
    )

    is_sunday = today.weekday() == 6
    sunday_special = session.get(Dish, menu.sunday_special_dish_id) if menu.sunday_special_dish_id else None
    sunday_special_candidates: list[Dish] = []
    if is_sunday:
        sunday_special_candidates = get_special_candidates(session, user.id, count=3, target_date=today)
        if sunday_special and sunday_special.id not in {c.id for c in sunday_special_candidates}:
            sunday_special_candidates = [sunday_special] + sunday_special_candidates

    all_dishes = session.exec(
        select(Dish).where(Dish.owner_id == user.id, Dish.active == True).order_by(Dish.name)  # noqa: E712
    ).all()
    whatsapp_text = _whatsapp_text(menu, breakfast, lunch, dinner, sunday_special) if (lunch and dinner) else ""

    return render(
        request,
        user,
        "index.html",
        {
            "menu": menu,
            "breakfast": breakfast,
            "lunch": lunch,
            "dinner": dinner,
            "breakfast_candidates": breakfast_candidates,
            "lunch_candidates": lunch_candidates,
            "dinner_candidates": dinner_candidates,
            "is_sunday": is_sunday,
            "sunday_special": sunday_special,
            "sunday_special_candidates": sunday_special_candidates,
            "all_dishes": all_dishes,
            "whatsapp_text": whatsapp_text,
            "today": today,
        },
    )


@app.get("/week")
def week_view(request: Request, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not session.exec(select(FamilyMember).where(FamilyMember.owner_id == user.id)).first():
        return RedirectResponse("/profile", status_code=303)
    plan = plan_week(session, user.id)
    return render(request, user, "week.html", {"plan": plan})


MEAL_FIELDS = {
    "breakfast": "breakfast_dish_id",
    "lunch": "lunch_dish_id",
    "dinner": "dinner_dish_id",
    "sunday_special": "sunday_special_dish_id",
}


@app.post("/menu/select")
def select_dish(
    request: Request, meal: str = Form(...), dish_id: int = Form(...), session: Session = Depends(get_session)
):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    # dish must belong to this user
    dish = session.exec(select(Dish).where(Dish.id == dish_id, Dish.owner_id == user.id)).first()
    if not dish:
        return RedirectResponse("/", status_code=303)
    today = date.today()
    menu = _get_or_create_menu(session, user.id, today)
    if meal in MEAL_FIELDS:
        setattr(menu, MEAL_FIELDS[meal], dish_id)
    menu.status = MenuStatus.draft
    session.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/menu/change")
def change_dish(request: Request, meal: str = Form(...), session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    today = date.today()
    menu = _get_or_create_menu(session, user.id, today)
    if meal in MEAL_FIELDS:
        setattr(menu, MEAL_FIELDS[meal], None)
    menu.status = MenuStatus.draft
    session.commit()
    return RedirectResponse("/", status_code=303)


def _dish_uses_ingredient(dish: Optional[Dish], ingredient_name: str) -> bool:
    if not dish or not dish.ingredients:
        return False
    return ingredient_name in {i.strip().lower() for i in dish.ingredients.split(",")}


@app.post("/menu/mark_unavailable")
def mark_unavailable(request: Request, ingredient_name: str = Form(...), session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    name = ingredient_name.strip().lower()
    existing = session.exec(
        select(OutOfStockIngredient).where(
            OutOfStockIngredient.owner_id == user.id, OutOfStockIngredient.ingredient_name == name
        )
    ).first()
    if not existing:
        session.add(OutOfStockIngredient(owner_id=user.id, ingredient_name=name, flagged_on=date.today()))
        session.commit()

    # if today's selected dish for any meal used this ingredient, clear it so fresh candidates show
    today = date.today()
    menu = session.exec(
        select(DailyMenu).where(DailyMenu.owner_id == user.id, DailyMenu.menu_date == today)
    ).first()
    if menu:
        changed = False
        for field in MEAL_FIELDS.values():
            dish_id = getattr(menu, field)
            if dish_id and _dish_uses_ingredient(session.get(Dish, dish_id), name):
                setattr(menu, field, None)
                changed = True
        if changed:
            session.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/menu/approve")
def approve_menu(request: Request, notes: str = Form(""), session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    today = date.today()
    menu = _get_or_create_menu(session, user.id, today)
    if not (menu.lunch_dish_id and menu.dinner_dish_id):
        return RedirectResponse("/", status_code=303)
    menu.notes = notes or None
    menu.status = MenuStatus.approved
    session.commit()
    for dish_id in (menu.breakfast_dish_id, menu.lunch_dish_id, menu.dinner_dish_id, menu.sunday_special_dish_id):
        if dish_id:
            session.add(CookedLog(owner_id=user.id, dish_id=dish_id, cooked_on=today))
    session.commit()
    return RedirectResponse("/", status_code=303)


# ---------- profile ----------


@app.get("/profile")
def profile(request: Request, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    members = session.exec(select(FamilyMember).where(FamilyMember.owner_id == user.id)).all()
    settings = session.exec(select(HouseholdSettings).where(HouseholdSettings.owner_id == user.id)).first()
    if settings is None:
        settings = HouseholdSettings(owner_id=user.id)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return render(request, user, "profile.html", {"members": members, "settings": settings})


@app.post("/profile/member/add")
def add_member(
    request: Request,
    name: str = Form(...),
    is_kid: bool = Form(False),
    diet: str = Form("veg"),
    high_protein_focus: bool = Form(False),
    restrictions: str = Form(""),
    session: Session = Depends(get_session),
):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    member = FamilyMember(
        owner_id=user.id,
        name=name,
        is_kid=is_kid,
        diet=DietType(diet),
        high_protein_focus=high_protein_focus,
        restrictions=restrictions or None,
    )
    session.add(member)
    session.commit()
    return RedirectResponse("/profile", status_code=303)


@app.post("/profile/member/{member_id}/delete")
def delete_member(request: Request, member_id: int, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    member = session.exec(
        select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.owner_id == user.id)
    ).first()
    if member:
        session.delete(member)
        session.commit()
    return RedirectResponse("/profile", status_code=303)


@app.post("/profile/settings")
def update_settings(
    request: Request,
    allow_non_veg: bool = Form(False),
    repeat_gap_days: int = Form(3),
    cuisine_preference: str = Form("universal"),
    session: Session = Depends(get_session),
):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    settings = session.exec(select(HouseholdSettings).where(HouseholdSettings.owner_id == user.id)).first()
    if settings is None:
        settings = HouseholdSettings(owner_id=user.id)
        session.add(settings)
    settings.allow_non_veg = allow_non_veg
    settings.repeat_gap_days = repeat_gap_days
    settings.cuisine_preference = CuisineRegion(cuisine_preference)
    session.commit()
    return RedirectResponse("/profile", status_code=303)


# ---------- dishes ----------


@app.get("/dishes")
def dishes(request: Request, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    all_dishes = session.exec(select(Dish).where(Dish.owner_id == user.id).order_by(Dish.name)).all()
    return render(request, user, "dishes.html", {"dishes": all_dishes})


@app.post("/dishes/add")
def add_dish(
    request: Request,
    name: str = Form(...),
    diet: str = Form("veg"),
    protein_source: str = Form(""),
    protein_grams: str = Form(""),
    calories: str = Form(""),
    meal_type: str = Form("any"),
    ingredients: str = Form(""),
    recipe_url: str = Form(""),
    image_url: str = Form(""),
    is_special: bool = Form(False),
    region: str = Form("universal"),
    session: Session = Depends(get_session),
):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    dish = Dish(
        owner_id=user.id,
        name=name,
        diet=DietType(diet),
        protein_source=protein_source or None,
        protein_grams=float(protein_grams) if protein_grams else None,
        calories=int(calories) if calories else None,
        meal_type=MealType(meal_type),
        ingredients=ingredients or None,
        recipe_url=recipe_url or None,
        image_url=image_url or None,
        is_special=is_special,
        region=CuisineRegion(region),
    )
    session.add(dish)
    session.commit()
    return RedirectResponse("/dishes", status_code=303)


@app.post("/dishes/{dish_id}/toggle")
def toggle_dish(request: Request, dish_id: int, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    dish = session.exec(select(Dish).where(Dish.id == dish_id, Dish.owner_id == user.id)).first()
    if dish:
        dish.active = not dish.active
        session.commit()
    return RedirectResponse("/dishes", status_code=303)


# ---------- pantry ----------


@app.get("/pantry")
def pantry(request: Request, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    items = session.exec(
        select(OutOfStockIngredient)
        .where(OutOfStockIngredient.owner_id == user.id)
        .order_by(OutOfStockIngredient.ingredient_name)
    ).all()
    today = date.today()
    return render(
        request, user, "pantry.html", {"items": items, "today": today, "expiry_days": OUT_OF_STOCK_EXPIRY_DAYS}
    )


@app.post("/pantry/add")
def add_out_of_stock(request: Request, ingredient_name: str = Form(...), session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    name = ingredient_name.strip().lower()
    existing = session.exec(
        select(OutOfStockIngredient).where(
            OutOfStockIngredient.owner_id == user.id, OutOfStockIngredient.ingredient_name == name
        )
    ).first()
    if not existing:
        session.add(OutOfStockIngredient(owner_id=user.id, ingredient_name=name, flagged_on=date.today()))
        session.commit()
    return RedirectResponse("/pantry", status_code=303)


@app.post("/pantry/{item_id}/delete")
def remove_out_of_stock(request: Request, item_id: int, session: Session = Depends(get_session)):
    user = _current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    item = session.exec(
        select(OutOfStockIngredient).where(OutOfStockIngredient.id == item_id, OutOfStockIngredient.owner_id == user.id)
    ).first()
    if item:
        session.delete(item)
        session.commit()
    return RedirectResponse("/pantry", status_code=303)
