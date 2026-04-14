from app.core.config import settings


def upload_image(file_bytes: bytes, filename: str) -> str:
    if not file_bytes:
        raise ValueError("Image file is empty")

    if settings.CLOUDINARY_CLOUD_NAME == "your_cloud_name":
        return f"https://example.com/uploads/{filename}"

    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        result = cloudinary.uploader.upload(file_bytes, public_id=filename, overwrite=True)
        return result["secure_url"]
    except Exception as exc:
        raise ValueError("Unable to upload image") from exc
