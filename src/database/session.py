import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()

DB_DRIVER = os.environ.get('DB_DRIVER')
DB_USER = os.environ.get('DB_USER')
DB_NAME = os.environ.get('DB_NAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')

DB_URL = f'{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'


engine = create_engine(
    DB_URL,
    pool_size=10,
    max_overflow=20,
    echo=False
)

Base = declarative_base()

Session = sessionmaker(
    autoflush=False,
    bind=engine
)

from .models import *