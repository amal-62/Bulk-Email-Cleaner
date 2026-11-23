import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import engine, Base
from app.routers import auth
from app.models import user
from app.routers import emails
from app.dependencies import get_current_user
from app.models.user import User

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(emails.router, prefix="/emails")

#check that the server is running
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}

#returns the profile of whoever is logged in
#if jwt tokein is missing request is rejected with a 401
@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture
    }