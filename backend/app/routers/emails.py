from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.gmail_service import fetch_emails, fetch_email_body

router = APIRouter(redirect_slashes=False)

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