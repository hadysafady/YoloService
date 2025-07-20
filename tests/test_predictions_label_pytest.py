import base64
import sqlite3
from app import DB_PATH, app, init_db
from fastapi.testclient import TestClient



client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_invaled_label():
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get("/predictions/label/blabla",headers=headers)
    assert response.status_code == 400
    
def test_valed_label():
    init_db()
    uid = "Test-label-valed-1234"
    lab = "knife"
    original_img = "323101.jpg"
    predicted_img = "323101.jpg"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ? ",(uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ? ",(uid,))

    with sqlite3.connect(DB_PATH) as conn :
        conn.execute("""INSERT INTO prediction_sessions (uid,original_image,predicted_image)
                     VALUES (?,?,?) """, (uid ,original_img,predicted_img ))
        conn.execute("""INSERT INTO detection_objects (prediction_uid,label)
                     VALUES (?,?) """,(uid, lab))
        
    headers = get_basic_auth_header("hadyy","safadyy")
    response = client.get(f"/predictions/label/{lab}",headers=headers)
    data = response.json()

    assert response.status_code == 200 
    assert len(data) == 1
    assert data[0]["uid"] == uid

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM detection_objects WHERE prediction_uid = ? ",(uid,))
        conn.execute("DELETE FROM prediction_sessions WHERE uid = ? ",(uid,))