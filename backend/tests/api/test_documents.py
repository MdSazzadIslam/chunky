from fastapi.testclient import TestClient

from app.main import app
from tests.fixtures import SAMPLE_PDF

client = TestClient(app)
USER_ID = "11111111-1111-1111-1111-111111111111"


def test_upload_requires_user_header() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.pdf", SAMPLE_PDF, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing X-User-Id header"


def test_upload_rejects_path_user_id() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        headers={"X-User-Id": "../etc"},
        files={"file": ("doc.pdf", SAMPLE_PDF, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid X-User-Id header"


def test_upload_rejects_non_pdf() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        headers={"X-User-Id": USER_ID},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Only application/pdf is allowed"


def test_upload_rejects_octet_stream() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        headers={"X-User-Id": USER_ID},
        files={"file": ("doc.pdf", SAMPLE_PDF, "application/octet-stream")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Only application/pdf is allowed"
