import base64
import os
import sqlite3
from app import DB_PATH, app, init_db
from fastapi.testclient import TestClient

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_invalid_image():
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get("/image/WrongType/SomeFile.jpg",headers=headers)
    assert response.status_code == 400

def test_valid_image():

    test_filename = "Example.jpg"
    test_filepath = os.path.join("uploads", "original", test_filename)
    with open(test_filepath, "wb") as f:
        f.write(b"dummy content")

    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get(f"/image/original/{test_filename}",headers=headers)
    assert response.status_code == 200 

    response = client.get("/image/original/SomeFile",headers=headers)
    assert response.status_code == 404

    os.remove(test_filepath)



