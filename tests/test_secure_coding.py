from pathlib import Path
from unittest.mock import patch


def test_validation_strict_schema(client):
    payload = {
        "name": "Test Film",
        "year": 2025,
        "kind": "film",
        "status": "planned",
        "extra_field": "should be rejected",
        "director": "Test Director",
    }
    response = client.post("/media", json=payload)
    assert response.status_code == 422
    error_msg = response.json()["detail"][0]["msg"].lower()
    assert "extra" in error_msg and "permitted" in error_msg


def test_validation_malicious_input(client):
    payload = {
        "name": "<script>alert('xss')</script>",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "director": "Test Director",
    }
    response = client.post("/media", json=payload)
    assert response.status_code == 422


def test_rfc7807_error_masking(client, db_session):
    with patch.object(
        db_session,
        "add",
        side_effect=Exception("Error with secret_token_12345 and user@example.com"),
    ):
        response = client.post(
            "/media",
            json={
                "name": "Test",
                "year": 2024,
                "kind": "film",
                "status": "planned",
                "director": "Test Director",
            },
        )
        assert response.status_code == 500
        data = response.json()
        assert "[TOKEN]" in data["detail"]
        assert "[EMAIL]" in data["detail"]


def test_file_upload_security_checks(client, db_session):
    media_data = {
        "name": "Test Film",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "director": "Test Director",
    }
    response = client.post("/media", json=media_data)
    media_id = response.json()["id"]

    large_content = b"x" * 6_000_000
    response = client.post(
        f"/media/{media_id}/attachment",
        files={"file": ("test.jpg", large_content, "image/jpeg")},
    )
    assert response.status_code == 413


def test_sql_injection_prevention(client):
    malicious_id = "1' OR '1'='1"
    response = client.get(f"/media/{malicious_id}")
    assert response.status_code in [422, 404]


def test_decimal_safe_serialization(client):
    payload = {
        "name": "Test Film",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "rating": 9.5,
        "director": "Test Director",
    }
    response = client.post("/media", json=payload)
    assert response.status_code == 201


def test_path_traversal_prevention(client, db_session):
    media_data = {
        "name": "Test Film",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "director": "Test Director",
    }
    response = client.post("/media", json=media_data)
    media_id = response.json()["id"]

    with patch("app.file_utils.FileSecurity.sniff_file_type") as mock_sniff:
        mock_sniff.return_value = "image/jpeg"

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/etc/passwd")
            response = client.post(
                f"/media/{media_id}/attachment",
                files={"file": ("test.jpg", b"fake content", "image/jpeg")},
            )
            assert response.status_code in [400, 500]


def test_symlink_protection(client, db_session):
    media_data = {
        "name": "Test Film",
        "year": 2024,
        "kind": "film",
        "status": "planned",
        "director": "Test Director",
    }
    response = client.post("/media", json=media_data)
    media_id = response.json()["id"]

    with patch("app.file_utils.FileSecurity.sniff_file_type") as mock_sniff:
        mock_sniff.return_value = "image/jpeg"

        with patch("pathlib.Path.is_symlink") as mock_symlink:
            mock_symlink.return_value = True
            response = client.post(
                f"/media/{media_id}/attachment",
                files={"file": ("test.jpg", b"fake content", "image/jpeg")},
            )
            assert response.status_code == 400
