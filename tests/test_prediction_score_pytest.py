import base64
import sqlite3
from app import DB_PATH, app, init_db
from fastapi.testclient import TestClient

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_score_not_inThe_range():
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get("/predictions/score/7",headers=headers)
    assert response.status_code == 400

def test_score_inThe_range():
    init_db()
    uid = "Test-Uid-for-score-123"
    minimum_score = 0.77
    original_img = "323101.jpg"
    predicted_img = "323101.jpg"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ? ",(uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ? ",(uid,))

    with sqlite3.connect(DB_PATH) as conn :
        conn.execute("""INSERT INTO prediction_sessions (uid, original_image, predicted_image)
                     VALUES (?,?,?) """, (uid, original_img, predicted_img ))
        conn.execute("""INSERT INTO detection_objects (prediction_uid, label, score)
                     VALUES (?,?,?) """,(uid ,"dog", minimum_score))
        
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get(f"/predictions/score/{minimum_score}",headers=headers)
    data = response.json()
    
    assert response.status_code == 200
    uids = [row["uid"] for row in data]
    assert uid in uids

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ? ",(uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ? ",(uid,))



