# Design

## Approach

Add a `POST /validate_dkim` endpoint that accepts the same `{"dkim_record": "..."}` JSON body used by all existing POST endpoints and returns `{"valid": true}` or `{"valid": false}`. Validity is defined as **syntactic only**: the tag list within the record must contain both a `v=DKIM1` tag and a `p=` tag (whose value may be empty — revoked keys are considered structurally valid per RFC 6376). No cryptographic parsing; no new dependencies.

A small private helper `is_valid_dkim(record)` extracts DKIM tags from the record string using the same token-splitting pattern already used by `parse_key_type`, then checks for the two required tags. This keeps all logic self-contained in `dkim.py` with no changes to `requirements.txt`.

The response shape uses `{"valid": true|false}` for both outcomes (HTTP 200 in both cases), treating validity as a data result rather than an error condition. Missing/malformed input returns `{"error": "missing dkim_record"}` with HTTP 400, consistent with `/dkim_key_type`.

Tests follow the pytest style of `tests/test_dkim_key_type.py` (most recent precedent).

---

## Changes by file

- **`dkim.py`** — add `is_valid_dkim(record)` helper and `POST /validate_dkim` route handler
- **`tests/test_validate_dkim.py`** — new pytest test file covering valid, invalid, revoked-key, and missing-input cases

---

## Step-by-step plan

1. **Add `is_valid_dkim(record)` helper to `dkim.py`** (insert after `parse_key_type`, before the first `@app.route`).

   Logic:
   ```python
   def is_valid_dkim(record):
       tags = {}
       for token in record.split():
           for part in token.split(';'):
               part = part.strip()
               if '=' in part:
                   key, _, val = part.partition('=')
                   tags[key.strip().lower()] = val.strip()
       return tags.get('v', '').upper() == 'DKIM1' and 'p' in tags
   ```
   - Splits on whitespace first (handles leading `<name> TXT` and trailing TTL tokens).
   - Splits each whitespace token on `;` (handles semicolon-separated tag lists like `v=DKIM1; k=rsa; p=ABC`).
   - Uses `partition('=')` so a bare `p=` (empty value, revoked key) still sets `tags['p']`.
   - Returns `True` only when both `v=DKIM1` and `p=` are present; `False` otherwise.

2. **Add `POST /validate_dkim` route to `dkim.py`** (append after the `/dkim_key_type` route):

   ```python
   @app.route('/validate_dkim', methods=['POST'])
   def validate_dkim():
       data = request.get_json()
       if not data or 'dkim_record' not in data:
           return jsonify({'error': 'missing dkim_record'}), 400
       valid = is_valid_dkim(data['dkim_record'])
       return jsonify({'valid': valid}), 200
   ```

3. **Create `tests/test_validate_dkim.py`** with pytest style matching `test_dkim_key_type.py`:

   - Inline `@pytest.fixture` named `client` (identical to the one in `test_dkim_key_type.py`)
   - Test cases listed in the Test plan below

---

## Test plan

**Existing tests**: no changes; all four existing test files continue to pass unchanged.

**New tests in `tests/test_validate_dkim.py`**:

| Test function | Input `dkim_record` | Expected response |
|---|---|---|
| `test_valid_rsa_record` | `"big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCD 6000"` | `200`, `{"valid": true}` |
| `test_valid_record_no_k_tag` | `"big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F 6000"` | `200`, `{"valid": true}` (k= is optional) |
| `test_invalid_missing_v_tag` | `"big-email._domainkey.example.com TXT k=rsa; p=ABCD 6000"` | `200`, `{"valid": false}` |
| `test_invalid_missing_p_tag` | `"big-email._domainkey.example.com TXT v=DKIM1; k=rsa 6000"` | `200`, `{"valid": false}` |
| `test_valid_revoked_key` | `"big-email._domainkey.example.com TXT v=DKIM1; p= 6000"` | `200`, `{"valid": true}` (empty p= is RFC-valid) |
| `test_missing_dkim_record_key_returns_400` | `{}` (no `dkim_record` key) | `400`, `{"error": "missing dkim_record"}` |

---

## Risks and open questions

1. **Revoked key (`p=` empty) returns `true`**: The design treats an empty `p=` as structurally valid (RFC 6376 §3.5 allows it). If the operator considers a revoked/unusable key "not valid" for this service's purposes, change the helper to require `tags.get('p') != ''`.

2. **`v=DKIM1` must be first tag (RFC strict)**: RFC 6376 §3.5 says "the `v=` tag MUST be the first tag". The current helper checks for its presence anywhere in the tag list, not positional order. This is consistent with how all other tag parsing works in this codebase. Tighten if strict RFC compliance is required.

3. **Records without the `<name> TXT` prefix**: The helper tolerates raw tag-only strings (e.g., `"v=DKIM1; p=ABC"`) because the token-splitting logic is tag-agnostic. This is a superset of the existing test format and should not cause problems.

4. **No new dependency on `requirements.txt`**: The design intentionally avoids adding `cryptography` or `dkimpy`. If the operator wants actual public key material validation (decoded base64 parses as a valid RSA/Ed25519 key), the design must be extended and `requirements.txt` updated.
