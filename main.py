from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import admin, auth, bookings, cars, enquiries, testimonials, users

app = FastAPI(title="FAST CARS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cars.router)
app.include_router(cars.admin_router)
app.include_router(bookings.router)
app.include_router(bookings.admin_router)
app.include_router(testimonials.router)
app.include_router(testimonials.admin_router)
app.include_router(enquiries.router)
app.include_router(users.admin_router)
app.include_router(admin.router)
