import sqlite3
from fastapi.testclient import TestClient
from app import app
import base64
from app import app, DB_PATH, init_db
import os

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def testPredictionUid_fakeUid():
    headers = get_basic_auth_header("hadyy" , "safadyy")
    response = client.get("/prediction/Fake-Uid",headers=headers)
    assert response.status_code == 404

def testPredictionUid_WithUid():
    init_db()
    uid = "Test-Example-123-123"
    original_img = "323101.jpg"
    predicted_img = "323101.jpg"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ?", (uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (uid,))

 # adding examples to the database
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""INSERT INTO prediction_sessions (uid,original_image,predicted_image)
                     VALUES (?,?,?)""",(uid , original_img , predicted_img) )
        
        conn.execute("""INSERT INTO detection_objects (prediction_uid,label,score,box)
                     VALUES (?,?,?,?) """,(uid , "dog" , 0.99 , str([100,100,200,200])))
        
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get(f"/prediction/{uid}",headers=headers)
    data = response.json()

    assert response.status_code == 200

    assert data["uid"] == uid
    assert len(data["detection_objects"]) == 1
    assert data["detection_objects"][0]["label"] == "dog"

 # remove the example data
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ?", (uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ?", (uid,))



    

    


