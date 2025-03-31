import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()


DATABASE_URL = os.getenv('DB_URL', 'sqlite:///recruiter.db')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()
