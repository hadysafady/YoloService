import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestPredictionCount(unittest.TestCase):
    def test_prediction_count_endpoint(self):
        response = client.get("/predictions/count")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), int)
 