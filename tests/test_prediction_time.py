import base64
import unittest
from fastapi.testclient import TestClient
from PIL import Image
import io

from app import app

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

class TestProcessingTime(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Create a simple test image
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.image_bytes = io.BytesIO()
        self.test_image.save(self.image_bytes, format='JPEG')
        self.image_bytes.seek(0)

    def test_predict_includes_processing_time(self):
        """Test that the predict endpoint returns processing time"""
        headers = get_basic_auth_header("hadyy" , "safadyy")
        response = self.client.post(
            "/predict",
            files={"file": ("test.jpg", self.image_bytes, "image/jpeg")},
            headers=headers
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify new field exists
        self.assertIn("time_took", data)
        self.assertIsInstance(data["time_took"], (int, float))
        self.assertGreater(data["time_took"], 0)