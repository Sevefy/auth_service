from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.schemas.user import UserSession

other_router = APIRouter(prefix="/v1/other")


@other_router.get("/", response_model=UserSession)
async def get_other(
        request: Request,
) -> JSONResponse | UserSession:
    session_cookie = request.cookies.get("sessionToken")
    if session_cookie is None:
        return JSONResponse(
            content="Нет сессии в куках",
            status_code=404
        )
    user_session: UserSession | None = request.app.state.user_session or None
    if user_session is None:
        return JSONResponse(
            content="Сессия не найдена или истекла",
            status_code=400
        )
    return user_session
