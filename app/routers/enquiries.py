from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.auth.dependencies import require_admin
from app.core.email import queue_email
from app.core.config import settings
from app.db import get_db, parse_object_id, stringify_id, utcnow
from app.schemas.enquiry import EnquiryCreate, EnquiryOut
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut


router = APIRouter(tags=["contact"])


def serialize_enquiry(document: dict) -> EnquiryOut:
    data = stringify_id(document)
    return EnquiryOut(
        _id=data["_id"],
        name=data["name"],
        email=data["email"],
        message=data["message"],
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
