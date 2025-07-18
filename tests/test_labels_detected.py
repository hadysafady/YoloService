import base64
import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestLabelsDetected(unittest.TestCase):
    def test_label_detected_endpoint(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/labels",headers=headers)
        self.assertEqual(response.status_code,200)
        self.assertIsInstance(response.json(),list)
        labels = response.json()
        for label in labels:
            self.assertEqual(type(label),str)