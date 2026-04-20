# Fast Cars Frontend Endpoint Note

This note is for the frontend developer and covers the backend routes currently ready for integration.

## Base Rules

- Base API URL: your FastAPI backend host, for example `http://localhost:8000`
- Auth: Bearer JWT
- User-protected routes require a logged-in user token
- Admin routes require a logged-in admin token
- Send protected requests with:

```http
Authorization: Bearer <access_token>
```

## Auth Routes

### `POST /api/auth/register`

Create a normal user account and return a JWT.

Example payload:

```json
{
  "name": "Jane Driver",
  "email": "jane@example.com",
  "phone": "09012345678",
  "password": "topsecret1"
}
```

Response:

```json
{
  "access_token": "jwt_here",
  "token_type": "bearer"
}
```

### `POST /api/auth/login`

Login for both normal users and admins.

Example payload:

```json
{
  "email": "jane@example.com",
  "password": "topsecret1"
}
```

### `POST /api/auth/token`

Alternative token route using OAuth form fields:

- `username`
- `password`

### `POST /api/auth/forgot-password`

Send reset flow email if the account exists.

Example payload:

```json
{
  "email": "jane@example.com"
}
```

### `POST /api/auth/reset-password`

Reset password using the token from the email flow.

Example payload:

```json
{
  "token": "reset_token_here",
  "new_password": "newsecret1"
}
```

### `GET /api/auth/me`

Protected route. Returns the current signed-in user.

## User Profile Routes

### `GET /api/users/me`

Protected route. Returns the current user profile.

### `PATCH /api/users/me`

Protected route. Update profile fields.

Example payload:

```json
{
  "name": "Jane Rider",
  "phone": "08123456789"
}
```

### `PATCH /api/users/me/password`

Protected route. Change password.

Example payload:

```json
{
  "current_password": "topsecret1",
  "new_password": "evenbetter9"
}
```

## Public Car Routes

### `GET /api/cars/`

Public route. Lists cars.

Supported query params:

- `category`
- `brand_id`
- `status_filter`

Example:

```text
/api/cars/?category=SUV&status_filter=active
```

### `GET /api/cars/{car_id}`

Public route. Get one car.

## Booking Routes

### `POST /api/bookings/`

Protected user route. Creates a booking with date conflict protection.

Example payload:

```json
{
  "car_id": "car_object_id",
  "start_date": "2026-04-20",
  "end_date": "2026-04-22"
}
```

Response includes:

- `_id`
- `user_id`
- `car_id`
- `start_date`
- `end_date`
- `total_days`
- `total_price`
- `status`
- `created_at`

### `GET /api/bookings/me`

Protected user route. Returns the current user booking history.

## Testimonial Routes

### `GET /api/testimonials/`

Public route. Returns only active testimonials.

### `POST /api/testimonials/`

Protected user route. Submit a testimonial.

Example payload:

```json
{
  "message": "Great service and smooth booking experience."
}
```

New testimonials are created inactive and require admin approval.

## Enquiry Routes

### `POST /api/enquiries`

Public route. Submit a contact/enquiry form.

Example payload:

```json
{
  "name": "Ada",
  "email": "ada@example.com",
  "phone": "08012345678",
  "message": "Do you offer weekend rentals?"
}
```

## Subscribe Route

### `POST /api/subscribe`

Public route. Add email to newsletter subscribers.

Example payload:

```json
{
  "email": "hello@example.com"
}
```

## Admin Login

Use the normal login route:

### `POST /api/auth/login`

Default seeded admin credentials:

```json
{
  "email": "admin@example.com",
  "password": "adminpass1"
}
```

## Admin Dashboard

### `GET /api/admin/dashboard`

Admin-only route. Returns summary counts:

```json
{
  "users": 0,
  "cars": 0,
  "bookings": 0,
  "pending_bookings": 0,
  "enquiries": 0,
  "subscribers": 0,
  "testimonials": 0
}
```

## Admin User Routes

### `GET /api/admin/users/`

Admin-only route. List all users.

### `GET /api/admin/users/{user_id}`

Admin-only route. Get one user.

## Admin Brand Routes

### `GET /api/admin/cars/brands`

Admin-only route. List all brands.

### `POST /api/admin/cars/brands`

Admin-only route. Create a brand.

Example payload:

```json
{
  "name": "Toyota",
  "logo_url": "https://example.com/logo.png"
}
```

### `PATCH /api/admin/cars/brands/{brand_id}`

Admin-only route. Update a brand.

### `DELETE /api/admin/cars/brands/{brand_id}`

Admin-only route. Delete a brand if no cars are linked to it.

## Admin Car Routes

### `GET /api/admin/cars/`

Admin-only route. List all cars, including inactive ones.

### `POST /api/admin/cars/`

Admin-only route. Create a car.

Example payload:

```json
{
  "brand_id": "brand_object_id",
  "name": "Toyota Corolla",
  "category": "Economy",
  "description": "Reliable city car",
  "images": ["https://example.com/car.jpg"],
  "daily_rate": 45,
  "seats": 5,
  "transmission": "Automatic",
  "fuel_type": "Petrol",
  "status": "active"
}
```

### `PUT /api/admin/cars/{car_id}`

Admin-only route. Update a car.

### `DELETE /api/admin/cars/{car_id}`

Admin-only route. Delete a car.

### `POST /api/admin/cars/upload`

Admin-only route. Upload image via multipart form.

Form field:

- `file`

Response:

```json
{
  "url": "https://cloudinary-url"
}
```

### `POST /api/admin/cars/upload-inline`

Admin-only route. Alternative upload route with form fields:

- `filename`
- `content`

## Admin Booking Routes

### `GET /api/admin/bookings/`

Admin-only route. List all bookings.

### `GET /api/admin/bookings/{booking_id}`

Admin-only route. Get one booking.

### `PATCH /api/admin/bookings/{booking_id}/confirm`

Admin-only route. Confirm a booking.

### `PATCH /api/admin/bookings/{booking_id}/cancel`

Admin-only route. Cancel a booking.

Booking records can include these extra admin-facing fields:

- `user_name`
- `user_email`
- `car_name`

## Admin Testimonial Routes

### `GET /api/admin/testimonials/`

Admin-only route. List all testimonials.

### `PATCH /api/admin/testimonials/{testimonial_id}`

Admin-only route. Approve or disable a testimonial.

Example payload:

```json
{
  "is_active": true
}
```

## Admin Enquiry Routes

### `GET /api/admin/enquiries`

Admin-only route. List all enquiries.

### `PATCH /api/admin/enquiries/{enquiry_id}`

Admin-only route. Update enquiry status.

Example payload:

```json
{
  "status": "read"
}
```

### `DELETE /api/admin/enquiries/{enquiry_id}`

Admin-only route. Delete an enquiry.

## Admin Subscriber Routes

### `GET /api/admin/subscribers`

Admin-only route. List all subscribers.

### `DELETE /api/admin/subscribers/{subscriber_id}`

Admin-only route. Delete a subscriber.

## Admin Site Content Routes

### `GET /api/admin/site-content`

Admin-only route. List editable site content items.

### `PATCH /api/admin/site-content/{key}`

Admin-only route. Upsert a content item by key.

Example payload:

```json
{
  "value": "Drive smarter with Fast Cars"
}
```

## Current Common Status Values

- Booking status: `pending`, `confirmed`, `cancelled`
- Car status: `active`, `inactive`
- Enquiry status: `unread`, `read`

## Frontend Notes

- MongoDB IDs are returned as strings
- Public and user apps can share the same auth endpoints
- The admin app uses the same login route as users, but must log in with an admin account
- Cloudinary upload is already wired on the backend through the admin car upload routes
