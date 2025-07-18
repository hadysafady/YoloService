import base64
import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestStatsEndpoint(unittest.TestCase):
    def test_stats_endpoint(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/stats",headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()

        self.assertIn("total_predictions", data)
        self.assertIn("average_confidence_score", data)
        self.assertIn("most_common_labels", data)

        self.assertIsInstance(data["total_predictions"], int)
        self.assertIsInstance(data["average_confidence_score"], (float,int))
        self.assertIsInstance(data["most_common_labels"], dict)

        self.assertGreaterEqual(data["total_predictions"], 0)
        self.assertGreaterEqual(data["average_confidence_score"], 0)
        self.assertLessEqual(data["average_confidence_score"], 1)

        labels = data["most_common_labels"]
        self.assertIsInstance(labels, dict)


