import unittest
import sqlite3
import os
from fastapi.testclient import TestClient
from app import app, DB_PATH

client = TestClient(app)

class TestPredictionCount(unittest.TestCase):
    def setUp(self):
        # הוסף prediction ידני ל-DB
        self.test_uid = "test-count-uid"
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO prediction_sessions (uid)
                VALUES (?)
            """, (self.test_uid,))

    def tearDown(self):
        # נקה אחרי הטסט כדי שלא יפריע לטסטים אחרים
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "DELETE FROM prediction_sessions WHERE uid = ?",
                (self.test_uid,)
            )

    def test_prediction_count_endpoint(self):
        response = client.get("/predictions/count")
        self.assertEqual(response.status_code, 200)
        api_count = response.json()
        self.assertIsInstance(api_count, int)

        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT COUNT(*) as cnt FROM prediction_sessions WHERE timestamp >= datetime('now', '-7 days')"
            ).fetchone()
            db_count = rows["cnt"]

        self.assertEqual(api_count, db_count)

 