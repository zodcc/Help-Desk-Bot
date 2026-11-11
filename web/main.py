from pathlib import Path
from typing import Annotated
from datetime import datetime, time as time_type
from fastapi import FastAPI, status, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.config import settings
from bot.database.session import async_session
from bot.database.models import User, Booking, Slot, BookingStatus, FAQ
from web.auth import create_access_token

app = FastAPI(title="HelpDeskBot Admin Panel")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

async def get_db():
    async with async_session() as session:
        yield session

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login")
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    if username != "admin" or password != settings.ADMIN_PASSWORD:
        return templates.TemplateResponse(
            request=request, name="login.html", context={"error": "Неверный логин или пароль"}
        )

    token = create_access_token(data={"sub": username})
    redirect_response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    redirect_response.set_cookie(key="access_token", value=token, httponly=True, max_age=86400)
    return redirect_response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    users_count = await db.scalar(select(func.count()).select_from(User))
    bookings_count = await db.scalar(select(func.count()).select_from(Booking))

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"users_count": users_count or 0, "bookings_count": bookings_count or 0}
    )

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    result = await db.execute(select(User).order_by(User.id.desc()))
    users_list = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="users.html", context={"users": users_list}
    )

@app.post("/users/anonymize/{user_id}")
async def anonymize_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user:
        user.full_name = "Анонимный пользователь"
        user.phone = None
        user.username = None
        user.consent_given = False
        await db.commit()
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    result = await db.execute(
        select(Booking)
        .options(joinedload(Booking.user), joinedload(Booking.slot))
        .order_by(Booking.id.desc())
    )
    bookings_list = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="bookings.html", context={"bookings": bookings_list}
    )

@app.post("/bookings/cancel/{booking_id}")
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    booking = await db.get(Booking, booking_id)
    if booking and booking.status == BookingStatus.CONFIRMED:
        booking.status = BookingStatus.CANCELLED
        slot = await db.get(Slot, booking.slot_id)
        if slot:
            slot.is_booked = False
        await db.commit()
    return RedirectResponse(url="/bookings", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    result = await db.execute(select(FAQ).order_by(FAQ.id.desc()))
    faqs_list = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="faq.html", context={"faqs": faqs_list}
    )

@app.post("/faq/add")
async def add_faq(
    keywords: Annotated[str, Form()],
    answer: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db)
):
    new_faq = FAQ(keywords=keywords, answer=answer)
    db.add(new_faq)
    await db.commit()
    return RedirectResponse(url="/faq", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/faq/delete/{faq_id}")
async def delete_faq(faq_id: int, db: AsyncSession = Depends(get_db)):
    faq = await db.get(FAQ, faq_id)
    if faq:
        await db.delete(faq)
        await db.commit()
    return RedirectResponse(url="/faq", status_code=status.HTTP_303_SEE_OTHER)

# ==========================================
# ЛОГИКА ДЛЯ РАЗДЕЛА "СЛОТЫ"
# ==========================================

@app.get("/slots", response_class=HTMLResponse)
async def slots_page(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Выводим слоты, сортируя по дате и времени.
    result = await db.execute(select(Slot).order_by(Slot.date, Slot.time))
    slots_list = result.scalars().all()

    return templates.TemplateResponse(
        request=request, name="slots.html", context={"slots": slots_list}
    )

@app.post("/slots/add")
async def add_slots(
    date_str: Annotated[str, Form(alias="date")], # Берем поле name="date" из формы
    times: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db)
):
    # Парсим дату из календаря (YYYY-MM-DD)
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Разбиваем строку времени по запятой
    time_strings = [t.strip() for t in times.split(",") if t.strip()]
    
    for ts in time_strings:
        try:
            # Парсим время (ЧЧ:ММ)
            t = datetime.strptime(ts, "%H:%M").time()
            
            # Проверяем, нет ли уже такого слота в базе, чтобы не дублировать
            exists = await db.execute(select(Slot).where(Slot.date == d, Slot.time == t))
            if not exists.scalar_one_or_none():
                db.add(Slot(date=d, time=t, is_booked=False))
        except ValueError:
            # Если админ ввел время неправильно, просто пропускаем
            pass
            
    await db.commit()
    return RedirectResponse(url="/slots", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/slots/delete/{slot_id}")
async def delete_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    slot = await db.get(Slot, slot_id)
    # Удаляем только если слот не занят
    if slot and not slot.is_booked:
        await db.delete(slot)
        await db.commit()
    return RedirectResponse(url="/slots", status_code=status.HTTP_303_SEE_OTHER)