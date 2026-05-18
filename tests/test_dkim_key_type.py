import json
import unittest
from dkim import app

class TestDkimKeyType(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_returns_200_with_explicit_k_tag(self):
        record = "big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCDEF 6000"
        response = self.client.post('/dkim_key_type', json={"dkim_record": record})
        self.assertEqual(response.status_code, 200)

    def test_returns_rsa_for_explicit_k_tag(self):
        record = "big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCDEF 6000"
        response = self.client.post('/dkim_key_type', json={"dkim_record": record})
        body = json.loads(response.data)
        self.assertEqual(body, {"key_type": "RSA"})

    def test_returns_rsa_default_when_k_tag_absent(self):
        record = "big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F709EF665853333EEC3F5ADE69A2362BECE40658267AB2FC3CB6CBE 6000"
        response = self.client.post('/dkim_key_type', json={"dkim_record": record})
        body = json.loads(response.data)
        self.assertEqual(body, {"key_type": "RSA"})

    def test_returns_400_when_dkim_record_missing(self):
        response = self.client.post('/dkim_key_type', json={"wrong_field": "value"})
        self.assertEqual(response.status_code, 400)
