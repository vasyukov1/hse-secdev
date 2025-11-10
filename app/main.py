import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .db import Base, SessionLocal, engine
from .errors import ProblemDetailException, problem, problem_detail_exception_handler

app = FastAPI(
    title="Media Wishlist",
    version="0.3.0",
    max_upload_size=1_000_000,
)

# Add securoty middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# Register exception handlers
app.add_exception_handler(ProblemDetailException, problem_detail_exception_handler)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail="The request contains invalid data",
        type_="https://tools.ietf.org/html/rfc9110#section-15.5.1",
        extras={"errors": exc.errors() if hasattr(exc, "errors") else []},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return problem(
        status_code=exc.status_code,
        title="HTTP Error",
        detail=exc.detail,
        type_="https://tools.ietf.org/html/rfc7231#section-6.5.1",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# --- CRUD endpoints ---
@app.post("/media", response_model=schemas.Media, status_code=201)
def create_media(media: schemas.MediaCreate, db: Session = Depends(get_db)):
    try:
        media = models.Media(**media.model_dump(exclude={"id"}))
        db.add(media)
        db.commit()
        db.refresh(media)
        return media
    except Exception as e:
        db.rollback()
        raise ProblemDetailException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Database Error",
            detail=str(e),
        )


@app.get("/media", response_model=List[schemas.Media])
def list_media(db: Session = Depends(get_db)):
    return db.query(models.Media).all()


@app.get("/media/{media_id}", response_model=schemas.Media)
def get_item(media_id: uuid.UUID, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise ProblemDetailException(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail="Media item not found",
        )
    return media


@app.put("/media/{media_id}", response_model=schemas.Media)
def update_media(
    media_id: uuid.UUID, updated_media: schemas.Media, db: Session = Depends(get_db)
):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise ProblemDetailException(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail="Media item not found",
        )

    try:
        update_data = updated_media.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(media, key, value)
        db.commit()
        db.refresh(media)
        return media
    except Exception as e:
        db.rollback()
        raise ProblemDetailException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Database Error",
            detail=str(e),
        )


@app.delete("/media/{media_id}")
def delete_media(media_id: uuid.UUID, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise ProblemDetailException(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail="Media item not found",
        )
    try:
        db.delete(media)
        db.commit()
        return {"status": "deleted"}
    except Exception as e:
        db.rollback()
        raise ProblemDetailException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Database Error",
            detail=str(e),
        )
