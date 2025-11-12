def test_large_request_rejected(client):
    """Test that large request bodies are rejected"""
    large_name = "x" * 1000000

    response = client.post(
        "/media",
        json={"name": large_name, "year": 2024, "kind": "film", "status": "planned"},
    )

    assert response.status_code in [413, 422]

    if response.status_code == 413:
        assert response.status_code == 413
    elif response.status_code == 422:
        data = response.json()
        assert "detail" in data


def test_valid_complex_json_accepted(client):
    """Test that valid complex JSON is accepted"""
    complex_data = {
        "name": "Complex Film",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "description": "A" * 500,
        "genres": ["action", "adventure", "sci-fi"],
        "director": "John " * 5 + "Doe",
        "rating": 9.5,
        "duration": 120,
    }

    response = client.post("/media", json=complex_data)
    assert response.status_code == 201
