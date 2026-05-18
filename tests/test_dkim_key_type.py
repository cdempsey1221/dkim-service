import pytest
from dkim import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_explicit_rsa_key_type(client):
    resp = client.post('/dkim_key_type', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCD 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'key_type': 'RSA'}


def test_missing_k_tag_defaults_to_rsa(client):
    resp = client.post('/dkim_key_type', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'key_type': 'RSA'}


def test_missing_dkim_record_key_returns_400(client):
    resp = client.post('/dkim_key_type', json={})
    assert resp.status_code == 400
    assert resp.get_json() == {'error': 'missing dkim_record'}
