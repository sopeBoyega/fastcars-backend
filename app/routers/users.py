from fastapi import APIRouter, Depends
from fastapi import HTTPException

from app.auth.dependencies import get_current_user, require_admin
from app.db import get_db, parse_object_id, stringify_id
from app.auth.utils import hash_password, verify_password
from app.schemas.user import ChangePasswordRequest, UserOut, UserUpdate


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


@router.patch("/me", response_model=UserOut)
async def update_my_profile(
    payload: UserUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": updates})
        current_user = await db.users.find_one({"_id": current_user["_id"]})
    return serialize_user(current_user)


@router.patch("/me/password")
async def change_my_password(
    payload: ChangePasswordRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if verify_password(payload.new_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="New password must be different from the current password")

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password)}},
    )
    return {"message": "Password updated successfully"}


@admin_router.get("/", response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def list_users(db=Depends(get_db)):
    users = await db.users.find({}).sort("name", 1).to_list(length=500)
    return [serialize_user(user) for user in users]


@admin_router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
async def get_user_detail(user_id: str, db=Depends(get_db)):
    try:
        object_id = parse_object_id(user_id, "user_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    user = await db.users.find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)
