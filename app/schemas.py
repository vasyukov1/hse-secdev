import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import Kind, Status


class MediaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: Optional[uuid.UUID] = None
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r'^[\w\s\-\.,!?()\[\]{}:;\'"@#$%&*+=]+$',
    )
    year: int = Field(..., gt=1800, le=2050)
    kind: Kind
    status: Status
    rating: Optional[float] = Field(None, ge=0, le=10, description="User rating 0–10")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Short description",
        pattern=r'^[\w\s\-\.,!?()\[\]{}:;\'"@#$%&*+=\n\r]*$',
    )
    genres: Optional[List[str]] = Field(
        None, description="List of genres", max_length=10
    )
    director: Optional[str] = Field(None, max_length=100, pattern=r"^[\w\s\-\.,]+$")
    duration: Optional[int] = Field(
        None, gt=0, le=1000, description="Duration in minutes"
    )
    url: Optional[str] = Field(None, description="Link to trailer or course page")

    @field_validator("year")
    @classmethod
    def validate_year_not_future(cls, v):
        current_year = datetime.now(timezone.utc).year
        if v > current_year:
            raise ValueError(
                f"Year cannot be in the future. Current year is {current_year}"
            )
        return v

    @field_validator("genres")
    @classmethod
    def validate_genres_length(cls, v):
        if v and len(v) > 10:
            raise ValueError("Maximum 10 genres allowed")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating_precision(cls, v):
        if v is not None:
            return Decimal(v).quantize(Decimal("0.1"))
        return v

    @model_validator(mode="after")
    def validate_film_specific_fields(self):
        if self.kind == Kind.film and not self.director:
            raise ValueError("Director is required for films")
        if self.kind == Kind.course and self.duration and self.duration > 600:
            raise ValueError("Course duration cannot exceed 600 minutes")
        return self


class MediaCreate(MediaBase):
    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if v is None or v == "":
            return v

        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        try:
            parsed = urlparse(v)

            suspicious_patterns = [
                r"localhost",
                r"127\.0\.0\.1",
                r"192\.168\.",
                r"10\.",
                r"172\.(1[6-9]|2[0-9]|3[0-1])\.",
                r"::1",
            ]

            hostname = parsed.hostname or ""
            for pattern in suspicious_patterns:
                if re.search(pattern, hostname, re.IGNORECASE):
                    raise ValueError("Internal URLs are not allowed")

            if len(v) > 2000:
                raise ValueError("URL too long (max 2000 characters)")

            return v

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid URL format: {str(e)}")


class Media(MediaBase):
    id: uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
