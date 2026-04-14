from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, require_admin
from app.core.email import queue_email
from app.db import get_db, parse_object_id, stringify_id, utcnow
from app.schemas.booking import BookingCreate, BookingOut, BookingStatus


router = APIRouter(prefix="/api/bookings", tags=["bookings"])
admin_router = APIRouter(prefix="/api/admin/bookings", tags=["admin-bookings"])


def serialize_booking(document: dict) -> BookingOut:
    data = stringify_id(document)
    return BookingOut(
        _id=data["_id"],
        user_id=str(data["user_id"]),
        car_id=str(data["car_id"]),
        start_date=data["start_date"],
        end_date=data["end_date"],
        total_days=data["total_days"],
        total_price=data["total_price"],
        status=data["status"],
        created_at=data["created_at"],
    )


async def get_car_for_booking(db, car_id: str) -> dict:
    try:
        object_id = parse_object_id(car_id, "car_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    car = await db.cars.find_one({"_id": object_id, "status": "active"})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


async def get_booking_or_404(db, booking_id: str) -> dict:
    try:
        object_id = parse_object_id(booking_id, "booking_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    booking = await db.bookings.find_one({"_id": object_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def calculate_total_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


async def has_booking_conflict(db, car_id, start_date: date, end_date: date) -> bool:
    query = {
        "car_id": car_id,
        "status": {"$in": [BookingStatus.pending.value, BookingStatus.confirmed.value]},
        "start_date": {"$lte": end_date},
        "end_date": {"$gte": start_date},
    }
    conflict = await db.bookings.find_one(query)
    return conflict is not None


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    car = await get_car_for_booking(db, payload.car_id)

    if await has_booking_conflict(db, car["_id"], payload.start_date, payload.end_date):
        raise HTTPException(status_code=409, detail="Car is already booked for the selected dates")

    total_days = calculate_total_days(payload.start_date, payload.end_date)
    document = {
        "user_id": current_user["_id"],
        "car_id": car["_id"],
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "total_days": total_days,
        "total_price": round(total_days * float(car["daily_rate"]), 2),
        "status": BookingStatus.pending.value,
        "created_at": utcnow(),
    }

    result = await db.bookings.insert_one(document)
    booking = await db.bookings.find_one({"_id": result.inserted_id})
    queue_email(
        background_tasks,
        subject="Fast Cars booking received",
        to_email=current_user["email"],
        body=f"Your booking for {car['name']} is pending confirmation.",
    )
    return serialize_booking(booking)


@router.get("/me", response_model=list[BookingOut])
async def list_my_bookings(db=Depends(get_db), current_user=Depends(get_current_user)):
    bookings = await db.bookings.find({"user_id": current_user["_id"]}).sort("created_at", -1).to_list(length=200)
    return [serialize_booking(booking) for booking in bookings]


@admin_router.get("/", response_model=list[BookingOut], dependencies=[Depends(require_admin)])
async def list_all_bookings(db=Depends(get_db)):
    bookings = await db.bookings.find({}).sort("created_at", -1).to_list(length=500)
    return [serialize_booking(booking) for booking in bookings]


@admin_router.patch("/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(
    booking_id: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    _=Depends(require_admin),
):
    booking = await get_booking_or_404(db, booking_id)
    await db.bookings.update_one({"_id": booking["_id"]}, {"$set": {"status": BookingStatus.confirmed.value}})
    booking = await db.bookings.find_one({"_id": booking["_id"]})
    user = await db.users.find_one({"_id": booking["user_id"]})
    if user:
        queue_email(
            background_tasks,
            subject="Fast Cars booking confirmed",
            to_email=user["email"],
            body="Your booking has been confirmed.",
        )
    return serialize_booking(booking)


@admin_router.patch("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(booking_id: str, db=Depends(get_db), _=Depends(require_admin)):
    booking = await get_booking_or_404(db, booking_id)
    await db.bookings.update_one({"_id": booking["_id"]}, {"$set": {"status": BookingStatus.cancelled.value}})
    booking = await db.bookings.find_one({"_id": booking["_id"]})
    return serialize_booking(booking)
