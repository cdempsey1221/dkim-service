# Design

## Approach

Add a `POST /dkim_key_type` endpoint to `dkim.py` backed by a new `parse_key_type(record)` helper. The helper scans the whitespace-tokenised record body for any token containing a `k=` tag (semicolon-separated), extracts its value, and uppercases it for the response. When the `k=` tag is absent, it defaults to `"RSA"` per RFC 6376 §3.3. Unparseable input (missing `dkim_record` key, non-string value) returns HTTP 400 with `{"error": "..."}`. The response on success is `{"key_type": "RSA"}`. A new test file `tests/test_dkim_key_type.py` covers the happy path (explicit `k=rsa`), the default-RSA path (no `k=` tag), and a 400 path (missing key in payload).

---

## Changes by file

- **`dkim.py`** — add `parse_key_type(record: str) -> str` helper and `POST /dkim_key_type` route
- **`tests/test_dkim_key_type.py`** — new test file with three test cases (explicit key type, absent key type defaults to RSA, missing payload key → 400)

---

## Step-by-step plan

1. **Add `parse_key_type` helper in `dkim.py`** (insert before the first `@app.route` decorator, after `split_key_by_val`):

   ```python
   def parse_key_type(record):
       for token in record.split():
           for tag in token.split(';'):
               tag = tag.strip()
               if tag.lower().startswith('k='):
                   return tag[2:].strip().upper()
       return 'RSA'  # RFC 6376 §3.3 default
   ```

   Logic: split the record on whitespace to get tokens, then split each token on `;` to get individual tag fragments, strip whitespace, find the one starting with `k=` (case-insensitive), and return its value uppercased. If no `k=` tag is found anywhere in the record, return `'RSA'`.

2. **Add `POST /dkim_key_type` route in `dkim.py`** (insert after the `split_by_value` route, before `healthz`):

   ```python
   @app.route('/dkim_key_type', methods=['POST'])
   def dkim_key_type():
       data = request.get_json()
       if not data or 'dkim_record' not in data:
           return jsonify({'error': 'missing dkim_record'}), 400
       key_type = parse_key_type(data['dkim_record'])
       return jsonify({'key_type': key_type}), 200
   ```

3. **Create `tests/test_dkim_key_type.py`** with three test cases (see Test plan below). Import pattern: `from dkim import app`.

---

## Test plan

**Existing tests** — no changes required; `test_healthz.py` and `test_split_key_by_val.py` are unaffected.

**New file: `tests/test_dkim_key_type.py`**

| Test method | Input `dkim_record` | Expected status | Expected body |
|---|---|---|---|
| `test_explicit_rsa_key_type` | `"big-email._domainkey.example.com TXT v=DKIM1; k=rsa; p=ABCD 6000"` | 200 | `{"key_type": "RSA"}` |
| `test_missing_k_tag_defaults_to_rsa` | `"big-email._domainkey.example.com TXT v=DKIM1; p=76E629F05F 6000"` (no `k=`) | 200 | `{"key_type": "RSA"}` |
| `test_missing_dkim_record_key_returns_400` | `{}` (empty JSON, no `dkim_record` key) | 400 | `{"error": "missing dkim_record"}` |

The first two tests exercise `parse_key_type` indirectly through the HTTP layer. A direct unit test of `parse_key_type` is not required by the goal, but the helper is simple enough that HTTP-layer coverage is sufficient.

---

## Risks and open questions

1. **HTTP method confirmed as POST** — consistent with `/split_by_value`; no ambiguity remains.

2. **Case of response value** — fixed as uppercase `"RSA"` (matching the task description's example). The helper uppercases whatever value is in `k=`, so `k=rsa`, `k=RSA`, and `k=Rsa` all return `"RSA"`.

3. **Default-RSA behaviour** — the existing canonical test record (`v=DKIM1; p=...` with no `k=`) has no `k=` tag. The helper defaults to `"RSA"` per RFC 6376. The `test_missing_k_tag_defaults_to_rsa` test uses this exact record, so the canonical fixture exercises the default path.

4. **No `ed25519` test case added** — the task only requires RSA; an `ed25519` case would be straightforward to add later by sending `k=ed25519` and expecting `{"key_type": "ED25519"}`, but it is out of scope here.

5. **`get_json()` returns `None` on malformed JSON** — the `if not data` guard in the route handles this; a `Content-Type: application/json` header is required by the test client calls (`.post(..., json={...})` sets it automatically).

6. **No 400 shape was previously established** — `split_by_value` crashes on bad input rather than returning 400. The `{"error": "..."}` shape introduced here is new; execute should not backfill error handling onto other routes.
