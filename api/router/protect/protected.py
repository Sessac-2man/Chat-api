from fastapi import APIRouter, Depends
from dto.user_schemas import User
from security.auth import get_current_user

protected_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

@protected_router.get("/my_account", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 반환
    """
    return current_user

