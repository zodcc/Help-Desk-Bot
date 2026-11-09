from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, status, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.session import async_session
from bot.database.models import User, Booking
from web.auth import create_access_token

app = FastAPI(title="HelpDeskBot Admin Panel")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Зависимость для получения сессии БД в веб-сервере
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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Делаем запросы к БД для подсчета статистики
    users_count = await db.scalar(select(func.count()).select_from(User))
    bookings_count = await db.scalar(select(func.count()).select_from(Booking))

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "users_count": users_count or 0,
            "bookings_count": bookings_count or 0
        }
    )