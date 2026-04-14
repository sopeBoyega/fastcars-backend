# Fast Cars Admin Frontend Endpoint Note

This note is for the admin developer only. All routes below are currently available for the admin app to implement.

Use:

`Authorization: Bearer <admin_token>`

If a normal user token is used on admin routes, the API returns:

```json
{
  "detail": "Admin access required"
}
```

## Admin Auth

There is no separate admin login endpoint yet. The admin app should currently use the normal auth login route, then call an admin route to confirm the logged-in user is actually an admin.

### `POST /api/auth/login`

Request:

```json
{
  "email": "admin@example.com",
  "password": "adminpassword"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Recommended admin auth flow:
- log in with `/api/auth/login`
- store the returned token
- immediately call `/api/admin/dashboard`
- if it returns `200`, user is admin
- if it returns `403`, block access to admin pages

## Dashboard

### `GET /api/admin/dashboard`

Purpose:
- load admin dashboard summary cards

Response:

```json
{
  "users": 10,
  "cars": 5,
  "bookings": 7,
  "pending_bookings": 2,
  "enquiries": 4,
  "subscribers": 12,
  "testimonials": 3
}
```

## User Management

### `GET /api/admin/users/`

Purpose:
- show all registered users in admin

Response:

```json
[
  {
    "_id": "user_id",
    "name": "Jane Driver",
    "email": "jane@example.com",
    "phone": "09012345678",
    "role": "user"
  }
]
```

## Booking Management

### `GET /api/admin/bookings/`

Purpose:
- list all bookings for admin review

Response:

```json
[
  {
    "_id": "booking_id",
    "user_id": "user_id",
    "car_id": "car_id",
    "start_date": "2026-04-15",
    "end_date": "2026-04-17",
    "total_days": 3,
    "total_price": 150.0,
    "status": "pending",
    "created_at": "2026-04-13T10:00:00Z"
  }
]
```

Booking statuses currently used:
- `pending`
- `confirmed`
- `cancelled`

### `PATCH /api/admin/bookings/{booking_id}/confirm`

Purpose:
- confirm a pending booking

Response:

```json
{
  "_id": "booking_id",
  "user_id": "user_id",
  "car_id": "car_id",
  "start_date": "2026-04-15",
  "end_date": "2026-04-17",
  "total_days": 3,
  "total_price": 150.0,
  "status": "confirmed",
  "created_at": "2026-04-13T10:00:00Z"
}
```

### `PATCH /api/admin/bookings/{booking_id}/cancel`

Purpose:
- cancel a booking

Response:

```json
{
  "_id": "booking_id",
  "user_id": "user_id",
  "car_id": "car_id",
  "start_date": "2026-04-15",
  "end_date": "2026-04-17",
  "total_days": 3,
  "total_price": 150.0,
  "status": "cancelled",
  "created_at": "2026-04-13T10:00:00Z"
}
```

## Brand Management

### `GET /api/admin/cars/brands`

Purpose:
- list all brands

Response:

```json
[
  {
    "id": "brand_id",
    "name": "Toyota",
    "logo_url": null,
    "created_at": "2026-04-13T10:00:00Z"
  }
]
```

### `POST /api/admin/cars/brands`

Purpose:
- create a brand

Request:

```json
{
  "name": "Toyota",
  "logo_url": null
}
```

Response:

```json
{
  "id": "brand_id",
  "name": "Toyota",
  "logo_url": null,
  "created_at": "2026-04-13T10:00:00Z"
}
```

### `PATCH /api/admin/cars/brands/{brand_id}`

Purpose:
- update a brand

Request:

```json
{
  "name": "Toyota Updated",
  "logo_url": "https://example.com/logo.png"
}
```

Response:

```json
{
  "id": "brand_id",
  "name": "Toyota Updated",
  "logo_url": "https://example.com/logo.png",
  "created_at": "2026-04-13T10:00:00Z"
}
```

### `DELETE /api/admin/cars/brands/{brand_id}`

Purpose:
- delete a brand

Success response:
- status `204`
- no response body

Possible error if brand has linked cars:

```json
{
  "detail": "Cannot delete a brand with linked cars"
}
```

## Car Management

### `POST /api/admin/cars/`

Purpose:
- create a car

Request:

```json
{
  "brand_id": "brand_id",
  "name": "Toyota Corolla",
  "category": "Economy",
  "description": "A reliable sedan for city and airport trips.",
  "images": [],
  "daily_rate": 50,
  "seats": 5,
  "transmission": "Automatic",
  "fuel_type": "Petrol",
  "status": "active"
}
```

Allowed enum values:
- `category`: `Economy`, `Premium`, `SUV`, `Luxury`
- `transmission`: `Automatic`, `Manual`
- `fuel_type`: `Petrol`, `Diesel`, `Electric`, `Hybrid`
- `status`: `active`, `inactive`

Response:

```json
{
  "id": "car_id",
  "brand_id": "brand_id",
  "name": "Toyota Corolla",
  "category": "Economy",
  "description": "A reliable sedan for city and airport trips.",
  "images": [],
  "daily_rate": 50.0,
  "seats": 5,
  "transmission": "Automatic",
  "fuel_type": "Petrol",
  "status": "active",
  "created_at": "2026-04-13T10:00:00Z"
}
```

### `PUT /api/admin/cars/{car_id}`

Purpose:
- update a car

Request:

```json
{
  "name": "Toyota Corolla 2026",
  "daily_rate": 55,
  "status": "inactive"
}
```

All fields are optional on update.

Response:

```json
{
  "id": "car_id",
  "brand_id": "brand_id",
  "name": "Toyota Corolla 2026",
  "category": "Economy",
  "description": "A reliable sedan for city and airport trips.",
  "images": [],
  "daily_rate": 55.0,
  "seats": 5,
  "transmission": "Automatic",
  "fuel_type": "Petrol",
  "status": "inactive",
  "created_at": "2026-04-13T10:00:00Z"
}
```

### `DELETE /api/admin/cars/{car_id}`

Purpose:
- delete a car

Success response:
- status `204`
- no response body

## Car Image Upload

### `POST /api/admin/cars/upload`

Purpose:
- upload image file for a car

Content type:
- `multipart/form-data`

Field:
- `file`

Response:

```json
{
  "url": "https://example.com/file.jpg"
}
```

### `POST /api/admin/cars/upload-inline`

Purpose:
- alternate upload route using form fields

Content type:
- `multipart/form-data`

Fields:
- `filename`
- `content`

Response:

```json
{
  "url": "https://example.com/file.jpg"
}
```

## Testimonial Moderation

### `GET /api/admin/testimonials/`

Purpose:
- list all testimonials, including inactive ones

Response:

```json
[
  {
    "_id": "testimonial_id",
    "user_id": "user_id",
    "user_name": "Jane Driver",
    "message": "Great experience and smooth booking process.",
    "is_active": false,
    "created_at": "2026-04-13T10:00:00Z"
  }
]
```

### `PATCH /api/admin/testimonials/{testimonial_id}`

Purpose:
- activate or deactivate testimonial

Request:

```json
{
  "is_active": true
}
```

Response:

```json
{
  "_id": "testimonial_id",
  "user_id": "user_id",
  "user_name": "Jane Driver",
  "message": "Great experience and smooth booking process.",
  "is_active": true,
  "created_at": "2026-04-13T10:00:00Z"
}
```

## Enquiry Management

### `GET /api/admin/enquiries`

Purpose:
- list all contact enquiries

Response:

```json
[
  {
    "_id": "enquiry_id",
    "name": "Ada",
    "email": "ada@example.com",
    "message": "I want to know if airport pickup is available.",
    "created_at": "2026-04-13T10:00:00Z"
  }
]
```

### `DELETE /api/admin/enquiries/{enquiry_id}`

Purpose:
- delete an enquiry after review

Success response:
- status `204`
- no response body

## Helpful Public Routes For Admin Screens

These are not admin-only, but the admin developer may still need them in management pages.

### `GET /api/cars/`

Purpose:
- fetch all active cars for reference
- supports query params `category`, `brand_id`, `status_filter`

### `GET /api/cars/{car_id}`

Purpose:
- fetch one car detail

### `GET /api/testimonials/`

Purpose:
- fetch public active testimonials

## Current Gaps

These are not available yet for admin:
- dedicated admin login route
- admin subscriber list endpoint
- admin car list endpoint that includes inactive cars directly
- admin user update/delete endpoints
- admin booking detail endpoint
