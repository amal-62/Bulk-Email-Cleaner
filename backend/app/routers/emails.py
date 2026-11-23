import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.email import Email
from app.services.gmail_service import fetch_emails, fetch_email_body, sync_emails, trash_messages, unsubscribe_senders

router = APIRouter(redirect_slashes=False)


class TrashRequest(BaseModel):
    sender_emails: List[str]


class UnsubscribeRequest(BaseModel):
    sender_emails: List[str]


@router.get("/")
def get_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the user's latest emails from Gmail.
    Protected — requires valid JWT.
    """
    try:
        emails = fetch_emails(current_user)
        return {"emails": emails}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_inbox(
    max_emails: int = 2000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Paginates through the user's Gmail inbox (up to max_emails),
    fetches metadata concurrently, and upserts into the emails table.
    Protected — requires valid JWT.
    """
    start = time.time()
    try:
        count = await sync_emails(current_user, db, max_emails=max_emails)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    elapsed = round(time.time() - start, 1)
    return {"synced": count, "seconds": elapsed}


@router.get("/grouped")
def get_grouped_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns emails from the DB grouped by sender_email, with a count per
    sender and whether any of their emails have a List-Unsubscribe header.
    This reads from the synced database, not live Gmail.
    Protected — requires valid JWT.
    """
    rows = (
        db.query(
            Email.sender_email,
            func.max(Email.sender_name).label("sender_name"),
            func.count(Email.id).label("email_count"),
            func.bool_or(Email.has_unsubscribe_header).label("can_unsubscribe"),
            func.max(Email.received_at).label("latest_received_at"),
        )
        .filter(
            Email.user_id == current_user.id,
            Email.is_trashed == False,
        )
        .group_by(Email.sender_email)
        .order_by(func.count(Email.id).desc())
        .all()
    )

    senders = [
        {
            "sender_email": row.sender_email,
            "sender_name": row.sender_name,
            "email_count": row.email_count,
            "can_unsubscribe": bool(row.can_unsubscribe),
            "latest_received_at": row.latest_received_at,
        }
        for row in rows
    ]

    return {"senders": senders, "total_senders": len(senders)}


@router.post("/trash")
async def trash_senders(
    body: TrashRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trashes every synced email from the given sender_emails in real Gmail,
    and marks the corresponding rows is_trashed=True in the DB.
    Protected — requires valid JWT.
    """
    if not body.sender_emails:
        raise HTTPException(status_code=400, detail="sender_emails cannot be empty")

    try:
        trashed_count, failed_count = await trash_messages(current_user, db, body.sender_emails)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"trashed": trashed_count, "failed": failed_count}


@router.post("/unsubscribe")
async def unsubscribe_from_senders(
    body: UnsubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Attempts to unsubscribe from each given sender using their real
    List-Unsubscribe mechanism (mailto or http). Protected — requires valid JWT.
    """
    if not body.sender_emails:
        raise HTTPException(status_code=400, detail="sender_emails cannot be empty")

    try:
        succeeded, failed = await unsubscribe_senders(current_user, db, body.sender_emails)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"unsubscribed": succeeded, "failed": failed}


@router.get("/{message_id}")
def get_email(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the full body of a specific email.
    Protected — requires valid JWT.
    """
    try:
        email = fetch_email_body(current_user, message_id)
        return email
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))