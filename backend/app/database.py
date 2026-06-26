# Import tools for connecting to and interacting with the database
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load the .env file so os.getenv() can read our secrets
load_dotenv()

# Read the database connection string from .env
# Format: postgresql://username@host/database_name
DATABASE_URL = os.getenv("DATABASE_URL")

#create the engine — this is the actual connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory for creating database sessions
# Each request gets its own session (like its own conversation with the DB)
# autocommit=False means we control when changes are saved
# autoflush=False means we control when data is sent to the DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all our database models will inherit from
# It keeps track of all the tables we define
Base = declarative_base()

# This function is called at the start of every API request that needs the DB
# 'yield' makes it a generator — it gives the session to the route handler
# The finally block ensures the session is ALWAYS closed after the request
# even if an error occurs
def get_db():
    db = SessionLocal()     # Open a new database session
    try:
        yield db            # Hand the session to the route that needs it
    finally:
        db.close()          # Always close the session when done