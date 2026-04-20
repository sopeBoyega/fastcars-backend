# Admin Frontend API Note

This note is for the admin frontend developer and reflects the current backend routes available in the FastAPI app.

## Base

- Base API URL: same backend host, for example `http://localhost:8000`
- Auth type: Bearer JWT
- Protected admin routes: all `/api/admin/*` routes require an authenticated admin user
- Login endpoint for admin token: `POST /api/auth/login`

## Admin Login

Use this payload to sign in from the admin frontend:

```json
{
  "email": "admin@example.com",
  "password": "adminpass1"
}
```

Successful response:

```json
{
  "access_token": "jwt_here",
  "token_type": "bearer"
}
```

Send the token as:

```http
Authorization: Bearer <access_token>
```

## Admin Dashboard

### `GET /api/admin/dashboard`

Returns top-level summary counts:

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

## Admin Cars

### `GET /api/admin/cars/`

Returns all cars, including inactive cars.

### `POST /api/admin/cars/brands`

Create a brand.

Example payload:

```json
{
  "name": "Toyota",
  "logo_url": "https://example.com/logo.png"
}
```

### `GET /api/admin/cars/brands`

List all brands.

### `PATCH /api/admin/cars/brands/{brand_id}`

Update a brand.

### `DELETE /api/admin/cars/brands/{brand_id}`

Deletes a brand only if no cars are linked to it.

### `POST /api/admin/cars/`

Create a car.

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

Update an existing car.

### `DELETE /api/admin/cars/{car_id}`

Delete a car.

### `POST /api/admin/cars/upload`

Multipart image upload for Cloudinary.

Form field:

- `file`

Response:

```json
{
  "url": "https://cloudinary-url"
}
```

### `POST /api/admin/cars/upload-inline`

Alternative upload route using form fields:

- `filename`
- `content`

## Admin Bookings

### `GET /api/admin/bookings/`

List all bookings.

Each booking can include:

- `booking_ref`
- `user_id`
- `customer`
- `user_email`
- `car_id`
- `car_name`
- `start_date`
- `end_date`
- `total_days`
- `total_cost`
- `status`
- `created_at`

### `GET /api/admin/bookings/{booking_id}`

Get one booking with enriched user/car info.

### `PATCH /api/admin/bookings/{booking_id}/confirm`

Confirms a booking and triggers confirmation email.

### `PATCH /api/admin/bookings/{booking_id}/cancel`

Cancels a booking.

## Admin Users

### `GET /api/admin/users/`

List all users.

### `GET /api/admin/users/{user_id}`

Get one user by ID.

## Admin Testimonials

### `GET /api/admin/testimonials/`

List all testimonials, including inactive ones.

### `PATCH /api/admin/testimonials/{testimonial_id}`

Approve or disable a testimonial.

Example payload:

```json
{
  "is_active": true
}
```

## Admin Enquiries

### `GET /api/admin/enquiries`

List all enquiries.

### `PATCH /api/admin/enquiries/{enquiry_id}`

Update enquiry status.

Example payload:

```json
{
  "status": "read"
}
```

Supported values are based on backend enum values such as `unread` and `read`.

### `DELETE /api/admin/enquiries/{enquiry_id}`

Delete an enquiry.

## Admin Subscribers

### `GET /api/admin/subscribers`

List newsletter subscribers.

### `DELETE /api/admin/subscribers/{subscriber_id}`

Delete a subscriber.

## Admin Site Content

### `GET /api/admin/site-content`

List editable site content entries.

### `PATCH /api/admin/site-content/{key}`

Create or update a content entry by key.

Example payload:

```json
{
  "value": "Drive smarter with Fast Cars"
}
```

Useful for admin-managed CMS-like text.

## Related Non-Admin Routes The Admin UI May Still Reuse

These are not admin-only, but may still be helpful in the admin app:

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/cars/`
- `GET /api/cars/{car_id}`

## Notes For Frontend Integration

- IDs are MongoDB object IDs returned as strings
- Most admin list routes return arrays
- Booking status values currently used by backend include `pending`, `confirmed`, and `cancelled`
- Car status currently uses values like `active` and `inactive`
- If an admin token is missing or belongs to a non-admin user, protected routes will reject the request
