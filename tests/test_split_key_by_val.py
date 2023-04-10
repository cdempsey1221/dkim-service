import unittest
from dkim import split_key_by_val

class TestSplitKeyByVal(unittest.TestCase):
    def test_split_key_by_val(self):
        key = "big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F709EF665853333EEC3F5ADE69A2362BECE40658267AB2FC3CB6CBE 6000"
        expected_output = {
            'record1': 'big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F709EF665853333EEC3F5ADE69A2362BECE40658267AB2FC3CB6CBE',
            'record2': 'big-email._domainkey.example.com TXT 6000'
        }
        self.assertEqual(split_key_by_val(key), expected_output)
