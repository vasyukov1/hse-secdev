import re
import uuid
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Kind, Status


class MediaBase(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    year: int = Field(..., gt=1800, le=2050)
    kind: Kind
    status: Status
    rating: Optional[float] = Field(None, ge=0, le=10, description="User rating 0–10")
    description: Optional[str] = Field(
        None, max_length=1000, description="Short description"
    )
    genres: Optional[List[str]] = Field(None, description="List of genres")
    director: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = Field(None, gt=0, description="Duration in minutes")
    url: Optional[str] = Field(None, description="Link to trailer or course page")


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

            return v

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid URL format: {str(e)}")


class Media(MediaBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
