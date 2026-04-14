from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.db import get_db


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def get_dashboard(db=Depends(get_db), _=Depends(require_admin)):
    return {
        "users": await db.users.count_documents({}),
        "cars": await db.cars.count_documents({}),
        "bookings": await db.bookings.count_documents({}),
        "pending_bookings": await db.bookings.count_documents({"status": "pending"}),
        "enquiries": await db.enquiries.count_documents({}),
        "subscribers": await db.subscribers.count_documents({}),
        "testimonials": await db.testimonials.count_documents({}),
    }
