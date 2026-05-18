import json
import unittest
from dkim import app

class TestReadyz(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_status_code(self):
        response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 200)

    def test_response_body(self):
        response = self.client.get('/readyz')
        body = json.loads(response.data)
        self.assertEqual(body, {"status": "ready"})

if __name__ == '__main__':
    unittest.main()
