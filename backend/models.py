from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)


class Note(Base):
    __tablename__ = "notes"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    note_id = Column(Integer, primary_key=True)
    note_date = Column(Text)
    note_text = Column(Text)

    user = relationship("User")
