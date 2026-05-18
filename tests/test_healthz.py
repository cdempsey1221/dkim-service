import json
import unittest
from dkim import app

class TestHealthz(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_healthz_returns_200(self):
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)

    def test_healthz_returns_json_body(self):
        response = self.client.get('/healthz')
        body = json.loads(response.data)
        self.assertEqual(body, {"status": "ok"})
