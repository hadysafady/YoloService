import unittest
from fastapi.testclient import TestClient
from app import app
import base64

client = TestClient(app)
 
def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestAuth(unittest.TestCase):
    def test_status_open(self):
        response = client.get("/health")  
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_predict_no_auth(self):
        with open("323101.jpg", "rb") as image_file:
            response = client.post(
                "/predict",
                files={"file": ("323101.jpg", image_file, "image/jpeg")}
            )
        self.assertEqual(response.status_code, 200)

    def test_predict_with_auth(self):
        headers = get_basic_auth_header("hadyy", "safadyy")
        with open("323101.jpg", "rb") as image_file:
            response = client.post(
                "/predict",
                files={"file": ("323101.jpg", image_file, "image/jpeg")},
                headers=headers
            )
        self.assertEqual(response.status_code, 200)

    def test_predict_with_wrongauth(self):
        headers = get_basic_auth_header("sad","saddsd")
        with open("323101.jpg", "rb") as image_file:
            response = client.post(
                "/predict",
                files={"file": ("323101.jpg", image_file, "image/jpeg")},
                headers=headers
            )
        self.assertEqual(response.status_code, 401)

    def test_prediction_count_with_auth(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/predictions/count",headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_prediction_count_with_wrongauth(self):
        headers = get_basic_auth_header("1sa2s" , "asdasdsa5")
        response = client.get("/predictions/count",headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_labels_with_auth(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/labels", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_labels_with_wrongauth(self):
        headers = get_basic_auth_header("1sa2s" , "asdasdsa5")
        response = client.get("/labels",headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_stats_with_auth(self):
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = client.get("/stats", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_stats_with_wrongauth(self):
        headers = get_basic_auth_header("1sa2s" , "asdasdsa5")
        response = client.get("/stats",headers=headers)
        self.assertEqual(response.status_code, 401)




if __name__ == "__main__":
    unittest.main()
