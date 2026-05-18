import pytest
from dkim import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_valid_rsa_record(client):
    resp = client.post('/validate_dkim', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCD 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'valid': True}


def test_valid_record_no_k_tag(client):
    resp = client.post('/validate_dkim', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'valid': True}


def test_invalid_missing_v_tag(client):
    resp = client.post('/validate_dkim', json={
        'dkim_record': 'big-email._domainkey.example.com TXT k=rsa; p=ABCD 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'valid': False}


def test_invalid_missing_p_tag(client):
    resp = client.post('/validate_dkim', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; k=rsa 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'valid': False}


def test_valid_revoked_key(client):
    resp = client.post('/validate_dkim', json={
        'dkim_record': 'big-email._domainkey.example.com TXT v=DKIM1; p= 6000'
    })
    assert resp.status_code == 200
    assert resp.get_json() == {'valid': True}


def test_missing_dkim_record_key_returns_400(client):
    resp = client.post('/validate_dkim', json={})
    assert resp.status_code == 400
    assert resp.get_json() == {'error': 'missing dkim_record'}
