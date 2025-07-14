import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestLabelsDetected(unittest.TestCase):
    def test_label_detected_endpoint(self):
        response = client.get("/labels")
        self.assertEqual(response.status_code,200)
        self.assertIsInstance(response.json(),list)
        labels = response.json()
        for label in labels:
            self.assertEqual(type(label),str)