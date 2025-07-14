import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestDeletePrediction(unittest.TestCase):
    def test_delete_prediction_endpoint(self):

        with open("323101.jpg", "rb") as f:
            response = client.post("/predict", files={"file": f})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        prediction_uid = data["prediction_uid"]
        self.assertIsInstance(prediction_uid, str)


        delete_response = client.delete(f"/prediction/{prediction_uid}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn("deleted successfully", delete_response.json()["detail"])

        get_response = client.get(f"/prediction/{prediction_uid}")
        self.assertEqual(get_response.status_code, 404)
