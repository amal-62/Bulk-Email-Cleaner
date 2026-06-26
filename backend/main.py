import os                           # For reading environment variables
from fastapi import FastAPI, Depends         # The main FastAPI class
from fastapi.middleware.cors import CORSMiddleware  # For allowing frontend requests
from dotenv import load_dotenv       # For reading our .env file
from app.database import engine, Base  # Our DB connection and table registry
from app.routers import auth         # Our auth routes
from app.models import user # register user model with base
from app.routers import emails
from app.routers import emails

# Load environment variables from .env into os.getenv()
load_dotenv()

# This reads all our model classes (like User) and creates their tables
# in PostgreSQL if they don't already exist
# Safe to run every time — it won't overwrite existing tables
Base.metadata.create_all(bind=engine)

# Create the FastAPI application instance
app = FastAPI(redirect_slashes=False)

# Tell the browser that requests from our React frontend are allowed
# Without this, the browser blocks requests between different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Our React dev server
    allow_credentials=True,   # Allow cookies and auth headers
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],      # Allow all request headers
)

# Register our auth router with a prefix
# This means all routes in auth.py will start with /auth
# So /google/login becomes /auth/google/login
app.include_router(auth.router, prefix="/auth")
app.include_router(emails.router, prefix="/emails")

# A simple health check endpoint to confirm the server is running
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}

#test route

from app.dependencies import get_current_user
from app.models.user import User

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Protected route — only works with a valid JWT.
    Returns the current logged-in user's info.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture
    }