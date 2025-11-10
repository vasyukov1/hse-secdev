import enum
import uuid

from sqlalchemy import JSON, Column, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .db import Base


# --- Enums for Media entity ---
class Kind(str, enum.Enum):
    film = "film"
    course = "course"


class Status(str, enum.Enum):
    planned = "planned"
    watching = "watching"
    completed = "completed"


# --- Media entity model --
class Media(Base):
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    kind = Column(Enum(Kind), nullable=False)
    status = Column(Enum(Status), nullable=False)
    rating = Column(Float)
    description = Column(Text)
    genres = Column(JSON, default=list)
    director = Column(String(100))
    duration = Column(Integer)
    url = Column(String)
