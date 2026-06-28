from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.responses import JSONResponse

from app.schemas.user import UserSession

other_router = APIRouter(prefix="/v1/other")


@other_router.get("/", response_model=UserSession)
def get_other(request: Request) -> JSONResponse | UserSession:
    session_cookie = request.cookies.get("sessionToken")
    if session_cookie is None:
        return JSONResponse(
            content="Нет сессии в куках",
            status_code=500
        )
    user_session = UserSession.model_validate_json(session_cookie)
    return user_session
