import os
import secrets
import traceback
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.models.user import User

router = APIRouter(redirect_slashes=False)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Temporary in-memory store for code verifiers
code_verifier_store = {}

def create_flow():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    return flow

def create_jwt(user_id: str, email: str) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expiry,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.get("/google/login")
def google_login():
    flow = create_flow()
    state = secrets.token_urlsafe(32)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state
    )
    # Store code verifier mapped to state
    code_verifier_store[state] = flow.code_verifier
    return RedirectResponse(url=auth_url, status_code=302)

@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Get all query parameters from the request
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            raise HTTPException(status_code=400, detail="No code provided")

        flow = create_flow()

        # Restore code verifier if we have one
        code_verifier = code_verifier_store.pop(state, None)
        if code_verifier:
            flow.code_verifier = code_verifier

        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Verify Google's ID token
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.access_token = credentials.token
            user.refresh_token = credentials.refresh_token or user.refresh_token
            user.name = name
            user.picture = picture
        else:
            user = User(
                email=email,
                name=name,
                picture=picture,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        token = create_jwt(str(user.id), user.email)

        # Redirect to frontend with JWT
        return RedirectResponse(
            url=f"http://localhost:5173?token={token}",
            status_code=302
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")