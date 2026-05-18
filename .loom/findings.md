# Findings

## Goal restated

Add a new endpoint to the Flask DKIM service that accepts a DKIM record payload and returns whether the record is a valid DKIM record, with at least one passing test.

---

## Relevant code locations

- `dkim.py` — the sole Flask application; defines all four existing routes and two helper functions
- `tests/test_dkim_key_type.py` — pytest-style tests for `POST /dkim_key_type`; most recent test file
- `tests/test_healthz.py` — unittest-style tests for `GET /healthz`
- `tests/test_readyz.py` — unittest-style tests for `GET /readyz`
- `tests/test_split_key_by_val.py` — unittest-style test of the `split_key_by_val` helper directly
- `requirements.txt` — Flask 2.2.3 plus transitive deps; no DKIM parsing library (e.g., `dkimpy`) present

---

## Current behaviour

### Routes in `dkim.py`

| Method | Path | Handler | Returns |
|--------|------|---------|---------|
| `POST` | `/split_by_value` | `split_by_value()` | `200` + `{"record1": ..., "record2": ...}` |
| `POST` | `/dkim_key_type` | `dkim_key_type()` | `200` + `{"key_type": "RSA"}`, or `400` + `{"error": "missing dkim_record"}` |
| `GET` | `/healthz` | `healthz()` | `200` + `{"status": "ok"}` |
| `GET` | `/readyz` | `readyz()` | `200` + `{"status": "ready"}` |

### Helper functions

**`split_key_by_val(key)`** (`dkim.py:28`) — splits a whitespace-tokenised DKIM record string into two TXT records by positional indexing. No validation.

**`parse_key_type(record)`** (`dkim.py:44`) — iterates whitespace-split tokens, then splits each by `;`, looks for a tag beginning with `k=`, and returns the uppercased value. Defaults to `'RSA'` (RFC 6376 §3.3 default) when the tag is absent.

### Input format established by existing tests

All POST endpoints receive `Content-Type: application/json` with a body keyed on `dkim_record`, e.g.:

```
"big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCD 6000"
```

The format is `<selector>._domainkey.<domain> TXT <dkim-tag-list> [ttl]`.

### Error handling convention

Only `/dkim_key_type` has input validation today. The pattern is:
```python
if not data or 'dkim_record' not in data:
    return jsonify({'error': 'missing dkim_record'}), 400
```
`/split_by_value` has no guard; a missing key raises an unhandled `KeyError`.

---

## Constraints and assumptions

### Language and framework
- Python 3.9, Flask 2.2.3 (pinned). No type hints, no dataclasses in use.
- Single file app (`dkim.py`); all routes are registered directly on the `app` object.
- `from flask import Flask, request, jsonify` already covers everything needed for a new POST route.

### No DKIM library available
`requirements.txt` contains only Flask and its transitive dependencies (click, colorama, itsdangerous, Jinja2, MarkupSafe, Werkzeug). There is no `dkimpy`, `dnspython`, or similar library. Validation must be implemented manually, or a new dependency must be added and pinned to `requirements.txt`.

### DKIM record validity (RFC 6376 §3.6.1)
A minimal syntactically valid DKIM public-key TXT record must:
1. Contain a `v=DKIM1` tag (required, must be first if present per RFC)
2. Contain a `p=` tag (required; value is base64-encoded public key, or empty to signal revocation)

Optional tags the endpoint may or may not check: `k=` (key type, default `rsa`), `h=` (hash algorithms), `t=` (flags), `s=` (service types), `n=` (notes).

The existing record strings in tests also include a leading `<name> TXT` prefix and an optional trailing TTL integer — the tag-parsing logic must account for tokens that are not `key=value` pairs.

### Testing conventions — mixed styles in repo
- `tests/test_healthz.py` and `tests/test_readyz.py`: `unittest.TestCase` subclass with `setUp` using `app.test_client()`.
- `tests/test_split_key_by_val.py`: `unittest.TestCase` testing a helper function directly.
- `tests/test_dkim_key_type.py` (most recent): **pytest** with a `@pytest.fixture` named `client`, using `app.config['TESTING'] = True` and `app.test_client()`. Assertions via plain `assert`.

The design phase must choose one style. The most recent test file uses pytest; `requirements.txt` does not list pytest explicitly but it is commonly available in the test environment (the `.gitignore` includes `.pytest_cache/`).

### Import pattern for tests
All test files import directly: `from dkim import app`. No `conftest.py` exists; the pytest fixture in `test_dkim_key_type.py` is defined inline.

### Error response schema
All errors use `{"error": "<message>"}` with HTTP `400`. This is the established contract.

### No `tests/__init__.py`
Tests directory has no `__init__.py`; discovery runs as `python -m unittest discover tests` or `pytest tests/`.

---

## Risks and open questions

### 1. Definition of "valid" — depth of validation
The goal says "actual valid DKIM record" but does not specify depth. Options from shallow to deep:
- **Syntactic only**: check that `v=DKIM1` and `p=` tags are present and non-absent.
- **Plus base64**: also verify that the `p=` value (if non-empty) is valid base64-encoded data.
- **Plus key parsing**: also verify the decoded bytes represent a parseable RSA/Ed25519 public key (would require `cryptography` library).

The codebase currently does no cryptographic operations. Adding the `cryptography` package is the only way to validate the actual key bytes. The design phase should decide whether "valid" means structurally present tags or also semantically correct key material.

### 2. Response shape on valid vs invalid input
Two common patterns:
- `200` with `{"valid": true|false}` for both outcomes (treats validity as data)
- `200` with `{"valid": true}` for valid; `422` or `400` with `{"error": "..."}` for invalid (treats invalidity as an error)

The existing endpoints do not have a boolean-result pattern. The design phase must pick one.

### 3. Response body on valid case
If `{"valid": true}` is chosen, should additional parsed fields be returned (e.g., `{"valid": true, "key_type": "RSA"}`), or is a bare boolean sufficient?

### 4. Endpoint naming
No strict naming convention exists. The two POST endpoints are `/split_by_value` (verb phrase) and `/dkim_key_type` (noun phrase). Candidates: `/validate_dkim`, `/dkim_validate`, `/dkim_valid`. The design phase should choose.

### 5. Handling the `<name> TXT` prefix and trailing TTL
The record strings used in all existing tests have the format `<name> TXT <tags> [ttl]`. The tag-parsing logic in `parse_key_type` relies on this implicitly (it skips non-`k=` tokens). A validation function must similarly tolerate leading `<name>`, `TXT`, and trailing TTL tokens without misidentifying them as DKIM tags. Whether records *without* this wrapper (raw tag lists like `v=DKIM1; p=ABC`) should also be accepted is an open question.

### 6. Empty `p=` (revoked key)
RFC 6376 allows `p=` with an empty value to signal key revocation. An empty `p=` is structurally valid per the RFC but the key is unusable. Whether this endpoint should return `{"valid": true}` or `{"valid": false}` for a revoked key must be decided.

### 7. Test file style decision
The repo mixes `unittest` and `pytest`. The last endpoint test (`test_dkim_key_type.py`) uses pytest. Following that most-recent precedent is the natural choice, but the design phase should confirm.
