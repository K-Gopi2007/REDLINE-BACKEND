import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestMain(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Redline")
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["docs"], "/docs")

    def test_docs(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_openapi_json(self):
        # We need to know what the openapi URL is. In main.py it's /api/v1/openapi.json
        from app.core.config import settings
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
