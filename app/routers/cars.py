from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.auth.dependencies import require_admin
from app.db import get_db, parse_object_id, stringify_id, utcnow
from app.schemas.car import BrandCreate, BrandOut, BrandUpdate, CarCreate, CarOut, CarUpdate
from app.utils.upload import upload_image


router = APIRouter(prefix="/api/cars", tags=["cars"])
admin_router = APIRouter(prefix="/api/admin/cars", tags=["admin-cars"])


def serialize_brand(document: dict) -> BrandOut:
    data = stringify_id(document)
    return BrandOut(
        id=data["_id"],
        name=data["name"],
        logo_url=data.get("logo_url"),
        created_at=data["created_at"],
    )


def serialize_car(document: dict) -> CarOut:
    data = stringify_id(document)
    return CarOut(
        id=data["_id"],
        brand_id=str(data["brand_id"]),
        brand_name=data.get("brand_name"),
        name=data["name"],
        category=data["category"],
        description=data["description"],
        images=data.get("images", []),
        daily_rate=data["daily_rate"],
        seats=data["seats"],
        transmission=data["transmission"],
        fuel_type=data["fuel_type"],
        status=data["status"],
        created_at=data["created_at"],
    )


async def get_brand_or_404(db, brand_id: str) -> dict:
    try:
        object_id = parse_object_id(brand_id, "brand_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    brand = await db.brands.find_one({"_id": object_id})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


async def get_car_or_404(db, car_id: str) -> dict:
    try:
        object_id = parse_object_id(car_id, "car_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    car = await db.cars.find_one({"_id": object_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.get("/", response_model=list[CarOut])
async def list_cars(
    category: str | None = None,
    brand_id: str | None = None,
    status_filter: str = "active",
    db=Depends(get_db),
):
    query: dict = {}
    if category:
        query["category"] = category
    if brand_id:
        try:
            query["brand_id"] = parse_object_id(brand_id, "brand_id")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    if status_filter:
        query["status"] = status_filter.lower()

    cars = await db.cars.find(query).sort("created_at", -1).to_list(length=200)
    return [serialize_car(car) for car in cars]


@router.get("/{car_id}", response_model=CarOut)
async def get_car(car_id: str, db=Depends(get_db)):
    car = await get_car_or_404(db, car_id)
    return serialize_car(car)


@admin_router.get("/brands", response_model=list[BrandOut], dependencies=[Depends(require_admin)])
async def list_brands(db=Depends(get_db)):
    brands = await db.brands.find({}).sort("name", 1).to_list(length=200)
    return [serialize_brand(brand) for brand in brands]


@admin_router.get("/", response_model=list[CarOut], dependencies=[Depends(require_admin)])
async def list_admin_cars(db=Depends(get_db)):
    cars = await db.cars.find({}).sort("created_at", -1).to_list(length=500)
    brand_ids = [car.get("brand_id") for car in cars if car.get("brand_id") is not None]
    brands = await db.brands.find({"_id": {"$in": brand_ids}}).to_list(length=500) if brand_ids else []
    brand_map = {brand["_id"]: brand for brand in brands}

    enriched_cars = []
    for car in cars:
        enriched = car.copy()
        brand = brand_map.get(car.get("brand_id"))
        if brand:
            enriched["brand_name"] = brand.get("name")
        enriched_cars.append(enriched)
    return [serialize_car(car) for car in enriched_cars]


@admin_router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand(payload: BrandCreate, db=Depends(get_db), _=Depends(require_admin)):
    existing = await db.brands.find_one({"name": payload.name})
    if existing:
        raise HTTPException(status_code=400, detail="Brand already exists")

    document = payload.model_dump()
    document["created_at"] = utcnow()
    result = await db.brands.insert_one(document)
    brand = await db.brands.find_one({"_id": result.inserted_id})
    return serialize_brand(brand)


@admin_router.patch("/brands/{brand_id}", response_model=BrandOut)
async def update_brand(brand_id: str, payload: BrandUpdate, db=Depends(get_db), _=Depends(require_admin)):
    brand = await get_brand_or_404(db, brand_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        await db.brands.update_one({"_id": brand["_id"]}, {"$set": updates})
        brand = await db.brands.find_one({"_id": brand["_id"]})
    return serialize_brand(brand)


@admin_router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(brand_id: str, db=Depends(get_db), _=Depends(require_admin)):
    brand = await get_brand_or_404(db, brand_id)
    linked_car = await db.cars.find_one({"brand_id": brand["_id"]})
    if linked_car:
        raise HTTPException(status_code=400, detail="Cannot delete a brand with linked cars")
    await db.brands.delete_one({"_id": brand["_id"]})


@admin_router.post("/", response_model=CarOut, status_code=status.HTTP_201_CREATED)
async def create_car(payload: CarCreate, db=Depends(get_db), _=Depends(require_admin)):
    brand = await get_brand_or_404(db, payload.brand_id)

    document = payload.model_dump()
    document["brand_id"] = brand["_id"]
    document["created_at"] = utcnow()
    result = await db.cars.insert_one(document)
    car = await db.cars.find_one({"_id": result.inserted_id})
    return serialize_car(car)


@admin_router.post("/upload", dependencies=[Depends(require_admin)])
async def upload_car_image(file: UploadFile = File(...)):
    file_bytes = await file.read()
    url = upload_image(file_bytes, file.filename or "car-image")
    return {"url": url}


@admin_router.post("/upload-inline", dependencies=[Depends(require_admin)])
async def upload_car_image_inline(filename: str = Form(...), content: str = Form(...)):
    url = upload_image(content.encode("utf-8"), filename)
    return {"url": url}


@admin_router.put("/{car_id}", response_model=CarOut)
async def update_car(car_id: str, payload: CarUpdate, db=Depends(get_db), _=Depends(require_admin)):
    car = await get_car_or_404(db, car_id)
    updates = payload.model_dump(exclude_unset=True)

    if "brand_id" in updates:
        brand = await get_brand_or_404(db, updates["brand_id"])
        updates["brand_id"] = brand["_id"]

    if updates:
        await db.cars.update_one({"_id": car["_id"]}, {"$set": updates})
        car = await db.cars.find_one({"_id": car["_id"]})
    return serialize_car(car)


@admin_router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(car_id: str, db=Depends(get_db), _=Depends(require_admin)):
    car = await get_car_or_404(db, car_id)
    await db.cars.delete_one({"_id": car["_id"]})
