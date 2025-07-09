import unittest
from fastapi.testclient import TestClient
from app import app

class TestPredictionCount(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_prediction_count_endpoint(self):
        """Ensure /prediction/count returns a valid response"""
        response = self.client.get("/prediction/count")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("prediction_count", data)
        self.assertIsInstance(data["prediction_count"], int)
        self.assertGreaterEqual(data["prediction_count"], 0)
