from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.gmail_service import fetch_emails, fetch_email_body
from app.services.ai_service import summarise_and_categorise_email, categorise_email_list

router = APIRouter(redirect_slashes=False)

class SummariseRequest(BaseModel):
    message_id: str

@router.post("/summarise")
def summarise_email(
    request: SummariseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches a specific email and returns an AI summary,
    category, priority score, and whether action is needed.
    """
    try:
        email = fetch_email_body(current_user, request.message_id)
        result = summarise_and_categorise_email(
            subject=email.get("subject", ""),
            sender="",
            body=email.get("body", email.get("snippet", ""))
        )
        return {
            "message_id": request.message_id,
            "subject": email.get("subject", ""),
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categorise-inbox")
def categorise_inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches latest 10 emails and categorises all of them using AI.
    Returns emails sorted by priority — highest first.
    """
    try:
        emails = fetch_emails(current_user, max_results=10)
        categorised = categorise_email_list(emails)
        categorised.sort(key=lambda x: int(x.get("priority", 1)), reverse=True)
        return {
            "emails": categorised,
            "total": len(categorised)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))