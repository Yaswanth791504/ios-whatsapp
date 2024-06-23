from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
load_dotenv()

# Create a connection to the database
engine = create_engine(
    'postgresql+psycopg2://postgres:yaswanth@localhost:5432/postgres', 
    pool_size=20,
    max_overflow=50, 
    pool_timeout=30, 
    pool_recycle=-1, 
    pool_pre_ping=True
)

session = sessionmaker(bind=engine)
Base = declarative_base()

print("Database connected successfully!")


from models import *

Base.metadata.create_all(engine)
