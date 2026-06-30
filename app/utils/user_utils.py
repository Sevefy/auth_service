from app.schemas.user import UserSession


def generate_key_by_user(user: UserSession) -> str:
    return str(user.token)
