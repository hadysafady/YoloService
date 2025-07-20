import base64
import os
import sqlite3
from fastapi.testclient import TestClient
from app import app, DB_PATH, init_db

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_prediction_image_full_coverage():
    init_db()
    uid = "test-image-uid-789"
    predicted_img = "323101.jpg"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (uid,))
        conn.execute("""
            INSERT INTO prediction_sessions (uid, predicted_image)
            VALUES (?, ?)
        """, (uid, predicted_img))

    headers = get_basic_auth_header("hadyy", "safadyy")

    headers["accept"] = "image/png"
    response = client.get(f"/prediction/{uid}/image", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    headers["accept"] = "image/jpeg"
    response = client.get(f"/prediction/{uid}/image", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

    headers["accept"] = "application/json"
    response = client.get(f"/prediction/{uid}/image", headers=headers)
    assert response.status_code == 406
    assert response.json()["detail"] == "Client does not accept an image format"

    response = client.get("/prediction/non-existent-uid/image", headers=headers)
    assert response.status_code == 404

    fake_uid = "test-image-uid-missing-file"
    fake_path = "non-existent-file.jpg"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (fake_uid,))
        conn.execute("""
            INSERT INTO prediction_sessions (uid, predicted_image)
            VALUES (?, ?)
        """, (fake_uid, fake_path))

    headers["accept"] = "image/jpeg"
    response = client.get(f"/prediction/{fake_uid}/image", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Predicted image file not found"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (fake_uid,))
