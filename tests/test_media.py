import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.main import app, get_db

# --- Test DB ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Create table
    Base.metadata.create_all(bind=engine)
    yield
    # Clear
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_create_media_success(client):
    payload = {
        "name": "Dracula",
        "year": 2025,
        "kind": "film",
        "status": "completed",
        "director": "Test Director",
        "description": (
            "A Love Tale is a 2025 English-language French gothic horror and "
            "romantic film written and directed by Luc Besson, based on the "
            "1897 novel Dracula by Bram Stoker"
        ),
    }
    response = client.post("/media", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data
    assert uuid.UUID(data["id"])
    assert 1800 < data["year"] <= 2025


def test_media_list(client):
    for i in range(2):
        payload = {
            "name": f"Film {i}",
            "year": 2000 + i,
            "kind": "film",
            "status": "planned",
            "director": f"Director {i}",
        }
        client.post("/media", json=payload)
    response = client.get("/media")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Film 0"
    assert data[1]["name"] == "Film 1"


def test_get_media_success_and_404(client):
    # Create media item
    payload = {
        "name": "Intellectual Data Analysis",
        "year": 2025,
        "kind": "course",
        "status": "watching",
        "director": "Test Director",
        "description": "The course about Machine Learning by Eugeny Sokolov.",
    }
    res_create = client.post("/media", json=payload)
    media_id = res_create.json()["id"]

    # Success GET
    res_get = client.get(f"/media/{media_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == media_id

    # Non-existent id
    fake_id = str(uuid.uuid4())
    res_404 = client.get(f"/media/{fake_id}")
    assert res_404.status_code == 404


def test_update_media_success_and_404(client):
    # Create media item
    payload = {
        "name": "Intellectual Data Analysis",
        "year": 2024,
        "kind": "course",
        "status": "watching",
        "description": "The course about Machine Learning by Eugeny Sokolov.",
    }
    res_create = client.post("/media", json=payload)
    media_id = res_create.json()["id"]

    # Updating
    update_payload = {
        "id": media_id,
        "name": "Intellectual Data Analysis",
        "year": 2025,
        "kind": "course",
        "status": "planned",
        "description": "The course about Deep Learning by Eugeny Sokolov.",
    }
    res_update = client.put(f"/media/{media_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["year"] == 2025
    assert res_update.json()["status"] == "planned"

    # Non-existent id
    fake_id = str(uuid.uuid4())
    res_404 = client.put(f"/media/{fake_id}", json=update_payload)
    assert res_404.status_code == 404


def test_delete_media_success_and_404(client):
    # Create media item
    payload = {
        "name": "F1",
        "year": 2025,
        "kind": "film",
        "status": "planned",
        "director": "Formula 1 Director",
        "description": "Du Du Du DUUU Max Verstappen",
    }
    res_create = client.post("/media", json=payload)
    media_id = res_create.json()["id"]

    # Success deleting
    res_delete = client.delete(f"/media/{media_id}")
    assert res_delete.status_code == 200
    assert res_delete.json() == {"status": "deleted"}

    # Repeat deleting
    res_404 = client.delete(f"/media/{media_id}")
    assert res_404.status_code == 404
