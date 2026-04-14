from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, require_admin
from app.db import get_db, parse_object_id, stringify_id, utcnow
from app.schemas.testimonial import TestimonialCreate, TestimonialOut, TestimonialUpdate


router = APIRouter(prefix="/api/testimonials", tags=["testimonials"])
admin_router = APIRouter(prefix="/api/admin/testimonials", tags=["admin-testimonials"])


def serialize_testimonial(document: dict) -> TestimonialOut:
    data = stringify_id(document)
    return TestimonialOut(
        _id=data["_id"],
        user_id=str(data["user_id"]),
        user_name=data["user_name"],
        message=data["message"],
        is_active=data["is_active"],
        created_at=data["created_at"],
    )


@router.get("/", response_model=list[TestimonialOut])
async def list_active_testimonials(db=Depends(get_db)):
    testimonials = await db.testimonials.find({"is_active": True}).sort("created_at", -1).to_list(length=200)
    return [serialize_testimonial(item) for item in testimonials]


@router.post("/", response_model=TestimonialOut, status_code=status.HTTP_201_CREATED)
async def create_testimonial(
    payload: TestimonialCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    document = {
        "user_id": current_user["_id"],
        "user_name": current_user["name"],
        "message": payload.message,
        "is_active": False,
        "created_at": utcnow(),
    }
    result = await db.testimonials.insert_one(document)
    testimonial = await db.testimonials.find_one({"_id": result.inserted_id})
    return serialize_testimonial(testimonial)


@admin_router.get("/", response_model=list[TestimonialOut], dependencies=[Depends(require_admin)])
async def list_all_testimonials(db=Depends(get_db)):
    testimonials = await db.testimonials.find({}).sort("created_at", -1).to_list(length=200)
    return [serialize_testimonial(item) for item in testimonials]


@admin_router.patch("/{testimonial_id}", response_model=TestimonialOut)
async def update_testimonial(
    testimonial_id: str,
    payload: TestimonialUpdate,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    try:
        object_id = parse_object_id(testimonial_id, "testimonial_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    testimonial = await db.testimonials.find_one({"_id": object_id})
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testimonial not found")

    await db.testimonials.update_one({"_id": object_id}, {"$set": {"is_active": payload.is_active}})
    testimonial = await db.testimonials.find_one({"_id": object_id})
    return serialize_testimonial(testimonial)
