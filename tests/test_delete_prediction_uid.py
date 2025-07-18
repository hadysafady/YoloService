import base64
import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestDeletePrediction(unittest.TestCase):
    def test_delete_prediction_endpoint(self):

        headers = get_basic_auth_header("hadyy" , "safadyy")
        with open("323101.jpg", "rb") as f:
            response = client.post("/predict", files={"file": f})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        prediction_uid = data["prediction_uid"]
        self.assertIsInstance(prediction_uid, str)


        delete_response = client.delete(f"/prediction/{prediction_uid}",headers=headers)
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn("deleted successfully", delete_response.json()["detail"])

        get_response = client.get(f"/prediction/{prediction_uid}",headers=headers)
        self.assertEqual(get_response.status_code, 404 or 401)
