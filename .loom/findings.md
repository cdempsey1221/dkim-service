# Findings

## Goal restated

Add a `POST /dkim_key_type` endpoint to `dkim.py` that accepts a JSON payload containing a DKIM record string, extracts the key type (e.g., `rsa`, `ed25519`) from the `k=` tag in the record, and returns HTTP 200 with the parsed key type. A matching test file must be added under `tests/`.

---

## Relevant code locations

- `dkim.py` — sole application file; defines Flask app, `split_key_by_val()` helper, `POST /split_by_value`, and `GET /healthz`
- `tests/test_healthz.py` — integration tests for `/healthz` using `app.test_client()`; canonical test template for new endpoint tests
- `tests/test_split_key_by_val.py` — unit tests for the `split_key_by_val` helper; canonical template for helper function tests
- `requirements.txt` — Flask 2.2.3, no validation library (Pydantic, marshmallow, etc.)

---

## Current behaviour

**Route pattern** (`dkim.py:44-53`):
```python
@app.route('/split_by_value', methods=['POST'])
def split_by_value():
    data = request.get_json()
    dkim_record = data['dkim_record']
    result = split_key_by_val(dkim_record)
    return jsonify(result)
```
Every POST endpoint: calls `request.get_json()`, accesses `data['dkim_record']` by direct dict key (no `.get()`, no 400 guard), calls a helper, returns `jsonify(result)` with an implicit 200.

**DKIM record format in the codebase** (from docstring and test fixture, `dkim.py:11`, `tests/test_split_key_by_val.py:6`):
```
big-email._domainkey.example.com TXT v=DKIM1; p=76E629... 6000
```
The record body is the semicolon-delimited tag list starting at `v=DKIM1`. Per RFC 6376, the `k=` tag identifies the key type and defaults to `rsa` when absent. The fixture in the existing test has **no `k=` tag**, meaning the default RSA case must be handled.

**Logging**: `app.logger.debug(...)` used in the helper; consistent style to follow.

**Test structure** (`tests/test_healthz.py`):
```python
import json, unittest
from dkim import app          # imports Flask app directly

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
```
POST endpoint tests will also use `self.client.post('/...', json={...})` (Flask test client supports `json=` kwarg for automatic Content-Type and serialisation).

---

## Constraints and assumptions

1. **Framework**: Flask 2.2.3 only. No additional dependencies may be added without updating `requirements.txt`.
2. **Payload field name**: Must accept `dkim_record` (same key used by `/split_by_value`) to be consistent with the rest of the service.
3. **DKIM `k=` tag parsing**: The tag list is embedded in the record string after `TXT `. Tags are semicolon-delimited (`v=DKIM1; k=rsa; p=...`). Key type lives in the `k=` tag value; RFC 6376 default is `rsa` when tag is absent.
4. **Response on success (200)**: Must return JSON (all other endpoints use `jsonify`). A reasonable shape is `{"key_type": "rsa"}`.
5. **Error handling**: Current codebase has **no** guard for missing keys or malformed input — a `KeyError` or `AttributeError` will produce an unhandled 500. The design phase must decide whether to maintain that pattern or introduce a 400 for missing/unparseable input.
6. **HTTP method**: Existing data-processing endpoints use `POST`; `/healthz` uses `GET`. The new endpoint receives a payload so `POST` is consistent.
7. **Test file location**: All tests live in `tests/`; no `conftest.py` or pytest configuration file — test runner appears to be `unittest` (or pytest with unittest-compatible classes).
8. **No `__init__.py`** in `tests/` — tests import directly from `dkim` (module on path).
9. **Python version**: Dockerfile specifies `python:3.9-alpine`.
10. **"pkayload"** in the goal is assumed to be a typo for "payload".

---

## Risks and open questions

1. **`k=` tag absent (RSA default)**: The existing test fixture has no `k=` tag. Should the endpoint return `{"key_type": "rsa"}` for records that omit `k=`, or return a non-200 because the tag is literally absent? The goal says "can be parsed from the payload", which is ambiguous when the tag is missing but the type is inferrable.

2. **Return 200 vs. 4xx on parse failure**: The goal says "returns 200 if … it can be parsed". This implies a non-200 (likely 400 or 422) when the tag cannot be found or the record is malformed — but the existing endpoints have no such guard. Design must decide the failure response shape and status code.

3. **Input format flexibility**: The record in the codebase is a full DNS zone-file line (`name TXT tags TTL`). Some callers may send only the TXT value portion (`v=DKIM1; k=rsa; p=…`). The parser must decide which format(s) to accept.

4. **Key type normalisation**: DKIM `k=` values are case-insensitive per RFC 6376. Should the response normalise to uppercase (`RSA`) matching the goal's example, or return the raw value (`rsa`)?

5. **Helper function vs. inline logic**: `split_key_by_val` extracts tokens positionally. Parsing `k=` by scanning semicolon-delimited tags is a different pattern — a small named helper (e.g., `get_key_type(record)`) would be consistent with the existing code style and make the function independently testable.

6. **Test coverage scope**: The goal specifies "a passing test" (singular). The design phase should decide whether to match the two-test pattern of `test_healthz.py` (status code + body) or add a third test for the parse-failure path if a 4xx is introduced.
