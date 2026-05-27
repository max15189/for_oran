from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "rsvp.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    token = Column(String, unique=True, nullable=False)
    invited_at = Column(DateTime, nullable=True)
    response = Column(String, nullable=True)   # 'yes' | 'no' | 'maybe'
    responded_at = Column(DateTime, nullable=True)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
