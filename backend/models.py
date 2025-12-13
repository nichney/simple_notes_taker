from sqlalchemy import Column, Integer, Text, ForeignKey, String, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    user_email = Column(String, nullable=False, unique=True, index=True)
    user_password = Column(String, nullable=False) # hashed password
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Note(Base):
    __tablename__ = "notes"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    note_id = Column(Integer, primary_key=True)
    note_date = Column(String)
    note_text = Column(Text)

    user = relationship("User")
