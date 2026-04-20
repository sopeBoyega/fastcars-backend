from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.auth.dependencies import require_admin
from app.core.email import queue_email
from app.core.config import settings
from app.db import get_db, parse_object_id, stringify_id, utcnow
from app.schemas.enquiry import EnquiryCreate, EnquiryOut, EnquiryStatus, EnquiryUpdate
from app.schemas.site_content import SiteContentOut, SiteContentUpdate
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut


router = APIRouter(tags=["contact"])


def serialize_enquiry(document: dict) -> EnquiryOut:
    data = stringify_id(document)
    return EnquiryOut(
        _id=data["_id"],
        name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        message=data["message"],
        status=data["status"],
        created_at=data["created_at"],
    )


def serialize_subscription(document: dict) -> SubscriptionOut:
    data = stringify_id(document)
    return SubscriptionOut(
        _id=data["_id"],
        email=data["email"],
        created_at=data["created_at"],
    )


@router.post("/api/enquiries", response_model=EnquiryOut, status_code=status.HTTP_201_CREATED)
async def create_enquiry(payload: EnquiryCreate, background_tasks: BackgroundTasks, db=Depends(get_db)):
    document = payload.model_dump()
    document["status"] = EnquiryStatus.unread.value
    document["created_at"] = utcnow()
    result = await db.enquiries.insert_one(document)
    enquiry = await db.enquiries.find_one({"_id": result.inserted_id})
    queue_email(
        background_tasks,
        subject="New Fast Cars enquiry",
        to_email=settings.EMAIL_USER,
        body=f"{payload.name} sent an enquiry: {payload.message}",
    )
    return serialize_enquiry(enquiry)


@router.get("/api/admin/enquiries", response_model=list[EnquiryOut], dependencies=[Depends(require_admin)])
async def list_enquiries(db=Depends(get_db)):
    enquiries = await db.enquiries.find({}).sort("created_at", -1).to_list(length=200)
    return [serialize_enquiry(item) for item in enquiries]


@router.patch("/api/admin/enquiries/{enquiry_id}", response_model=EnquiryOut, dependencies=[Depends(require_admin)])
async def update_enquiry(enquiry_id: str, payload: EnquiryUpdate, db=Depends(get_db)):
    try:
        object_id = parse_object_id(enquiry_id, "enquiry_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    enquiry = await db.enquiries.find_one({"_id": object_id})
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    await db.enquiries.update_one({"_id": object_id}, {"$set": {"status": payload.status.value}})
    enquiry = await db.enquiries.find_one({"_id": object_id})
    return serialize_enquiry(enquiry)


@router.delete("/api/admin/enquiries/{enquiry_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_enquiry(enquiry_id: str, db=Depends(get_db)):
    try:
        object_id = parse_object_id(enquiry_id, "enquiry_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    enquiry = await db.enquiries.find_one({"_id": object_id})
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    await db.enquiries.delete_one({"_id": object_id})


@router.post("/api/subscribe", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def subscribe(payload: SubscriptionCreate, db=Depends(get_db)):
    existing = await db.subscribers.find_one({"email": payload.email})
    if existing:
        return serialize_subscription(existing)

    document = payload.model_dump()
    document["created_at"] = utcnow()
    result = await db.subscribers.insert_one(document)
    subscription = await db.subscribers.find_one({"_id": result.inserted_id})
    return serialize_subscription(subscription)


@router.get("/api/admin/subscribers", response_model=list[SubscriptionOut], dependencies=[Depends(require_admin)])
async def list_subscribers(db=Depends(get_db)):
    subscribers = await db.subscribers.find({}).sort("created_at", -1).to_list(length=500)
    return [serialize_subscription(item) for item in subscribers]


@router.delete("/api/admin/subscribers/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_subscriber(subscriber_id: str, db=Depends(get_db)):
    try:
        object_id = parse_object_id(subscriber_id, "subscriber_id")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    subscriber = await db.subscribers.find_one({"_id": object_id})
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    await db.subscribers.delete_one({"_id": object_id})


def serialize_site_content(document: dict) -> SiteContentOut:
    data = stringify_id(document)
    return SiteContentOut(
        _id=data["_id"],
        key=data["key"],
        value=data["value"],
        updated_at=data["updated_at"],
    )


@router.patch("/api/admin/site-content/{key}", response_model=SiteContentOut, dependencies=[Depends(require_admin)])
async def update_site_content(key: str, payload: SiteContentUpdate, db=Depends(get_db)):
    normalized_key = key.strip()
    if not normalized_key:
        raise HTTPException(status_code=400, detail="Site content key is required")

    await db.site_content.update_one(
        {"key": normalized_key},
        {"$set": {"value": payload.value, "updated_at": utcnow()}},
        upsert=True,
    )
    content = await db.site_content.find_one({"key": normalized_key})
    return serialize_site_content(content)


@router.get("/api/admin/site-content", response_model=list[SiteContentOut], dependencies=[Depends(require_admin)])
async def list_site_content(db=Depends(get_db)):
    content_items = await db.site_content.find({}).sort("key", 1).to_list(length=500)
    return [serialize_site_content(item) for item in content_items]
