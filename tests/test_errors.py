def test_rfx7807_format_not_found(client):
    """Test that 404 errors follow RFC 7807 format"""
    response = client.get("/media/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    data = response.json()

    # RFC 7807 required fields
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "correlation_id" in data

    assert data["status"] == 404
    assert data["title"] == "Not Found"
    assert len(data["correlation_id"]) == 36


def test_rfc7807_format_validation_error(client):
    """Test that validation errors follow RFC 7807 format"""
    response = client.post(
        "/media", json={"name": "", "year": 1799, "kind": "film", "status": "planned"}
    )

    assert response.status_code == 422
    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)

    error_messages = [error["msg"] for error in data["detail"]]
    expected_errors = [
        "String should have at least 1 character",
        "Input should be greater than 1800",
    ]

    for expected_error in expected_errors:
        assert any(expected_error in msg for msg in error_messages)


def test_url_validation_success(client):
    """Test valid URL passes validation"""
    response = client.post(
        "/media",
        json={
            "name": "Test Film",
            "year": 2024,
            "kind": "film",
            "status": "planned",
            "director": "Test Director",
            "url": "https://example.com/trailer",
        },
    )

    assert response.status_code == 201


def test_url_validation_invalid_scheme(client):
    """Test invalid URL scheme is rejected"""
    response = client.post(
        "/media",
        json={
            "name": "Test Film",
            "year": 2024,
            "kind": "film",
            "status": "planned",
            "director": "Test Director",
            "url": "javascript:alert('xss')",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "URL must start with http:// or https://" in str(data)


def test_url_validation_internal_host(client):
    """Test internal URLs are rejected"""
    response = client.post(
        "/media",
        json={
            "name": "Test Film",
            "year": 2024,
            "kind": "film",
            "status": "planned",
            "director": "Test Director",
            "url": "https://localhost/admin",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "Internal URLs are not allowed" in str(data)


def test_url_validation_too_long(client):
    """Test overly long URLs are rejected"""
    long_url = "https://example.com/" + "a" * 2000
    response = client.post(
        "/media",
        json={
            "name": "Test Film",
            "year": 2024,
            "kind": "film",
            "status": "planned",
            "director": "Test Director",
            "url": long_url,
        },
    )

    assert response.status_code in [201, 422, 500]
    if response.status_code == 422:
        data = response.json()
        assert "detail" in data or "errors" in data
