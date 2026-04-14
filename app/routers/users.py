from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_admin
from app.db import get_db, stringify_id
from app.schemas.user import UserOut


router = APIRouter(prefix="/api/users", tags=["users"])
admin_router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def serialize_user(document: dict) -> UserOut:
    data = stringify_id(document)
    return UserOut(
        _id=data["_id"],
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        role=data["role"],
    )


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user=Depends(get_current_user)):
    return serialize_user(current_user)


@admin_router.get("/", response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def list_users(db=Depends(get_db)):
    users = await db.users.find({}).sort("name", 1).to_list(length=500)
    return [serialize_user(user) for user in users]
