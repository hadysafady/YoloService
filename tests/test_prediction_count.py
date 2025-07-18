import base64
import unittest
import sqlite3
import os
from fastapi.testclient import TestClient
from app import app, DB_PATH

client = TestClient(app)
def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestPredictionCount(unittest.TestCase):
    def setUp(self):
        self.test_uid = "test-count-uid"
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO prediction_sessions (uid)
                VALUES (?)
            """, (self.test_uid,))

    def tearDown(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "DELETE FROM prediction_sessions WHERE uid = ?",
                (self.test_uid,)
            )

    def test_prediction_count_endpoint(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/predictions/count",headers=headers)
        self.assertEqual(response.status_code, 200)
        api_count = response.json()
        self.assertIsInstance(api_count, int)

        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT COUNT(*) as cnt FROM prediction_sessions WHERE timestamp >= datetime('now', '-7 days')"
            ).fetchone()
            db_count = rows[0]

        self.assertEqual(api_count, db_count)

 