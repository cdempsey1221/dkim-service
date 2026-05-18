# Design

## Approach

Add a `POST /dkim_key_type` endpoint to `dkim.py` backed by a new `get_key_type(record)` helper. The helper extracts the tag-list portion of the DKIM record string (everything after the `TXT` token, up to any trailing TTL integer), splits on semicolons, scans for a `k=` tag, and returns the value normalised to uppercase. If the `k=` tag is absent the RFC 6376 default `"RSA"` is returned — this is correct behaviour and counts as a successful parse. The endpoint returns HTTP 200 with `{"key_type": "<VALUE>"}` on success, and HTTP 400 with `{"error": "<reason>"}` when the payload is missing the required field or no tag-list can be found. A companion test file covers status code, response body, the absent-`k=`-tag default, and the missing-field 400.

Key design decisions:
- **Return RSA default when `k=` is absent**: the existing test fixture has no `k=` tag; treating "absent" as "unparseable" would make the most realistic fixture a failure case, which is wrong.
- **Return uppercase**: the goal example says `RSA`; uppercase is unambiguous and consistent regardless of what the sender sends.
- **Introduce a 400 guard for missing `dkim_record` key**: the goal says "returns 200 if … it can be parsed", implying a non-200 otherwise. A 400 is the correct semantic for a bad request. This is a deliberate, narrow deviation from the no-guard pattern on `/split_by_value` — only for the missing-field case, not for other malformed input.
- **Helper function**: keeps the route handler thin and makes the parsing logic independently testable, consistent with the existing `split_key_by_val` pattern.
- **No new dependencies**: pure string operations only.

---

## Changes by file

- **`dkim.py`** — add `get_key_type(record: str) -> str` helper and `POST /dkim_key_type` route handler
- **`tests/test_dkim_key_type.py`** — new test file with four tests covering the endpoint (200 with explicit `k=rsa`, 200 with `k=` absent defaulting to RSA, 200 with uppercase normalisation, 400 for missing `dkim_record` field)

---

## Step-by-step plan

1. **Add `get_key_type` helper to `dkim.py`** (insert after `split_key_by_val`, before the route definitions):

   ```python
   def get_key_type(record):
       # Isolate the TXT tag-list: drop the leading "name TXT" tokens and any trailing TTL
       parts = record.split()
       try:
           txt_index = next(i for i, p in enumerate(parts) if p.upper() == 'TXT')
       except StopIteration:
           # No TXT token — treat the whole string as the tag-list
           txt_index = -1
       tag_string = ' '.join(parts[txt_index + 1:])
       # Strip trailing TTL (a bare integer at the end)
       tag_parts = tag_string.rsplit(None, 1)
       if len(tag_parts) == 2 and tag_parts[1].isdigit():
           tag_string = tag_parts[0]
       # Parse semicolon-delimited tags
       for tag in tag_string.split(';'):
           tag = tag.strip()
           if tag.lower().startswith('k='):
               return tag[2:].strip().upper()
       # RFC 6376 §3.5: k= defaults to rsa
       return 'RSA'
   ```

   Logic walkthrough:
   - Finds the `TXT` token (case-insensitive) and takes everything after it as the tag-list.
   - Strips a trailing bare integer (the TTL) so `p=...` values that contain digits don't get accidentally trimmed.
   - Iterates tags split by `;`, matches the first tag whose key is `k` (case-insensitive), returns the value uppercased.
   - Falls back to `'RSA'` if no `k=` tag is found.
   - If no `TXT` token exists, treats `txt_index = -1` so `parts[0:]` is the full string — gracefully handles bare tag-list input.

2. **Add `POST /dkim_key_type` route to `dkim.py`** (append before `if __name__ == '__main__':`):

   ```python
   @app.route('/dkim_key_type', methods=['POST'])
   def dkim_key_type():
       data = request.get_json()
       if not data or 'dkim_record' not in data:
           return jsonify({"error": "missing dkim_record"}), 400
       key_type = get_key_type(data['dkim_record'])
       app.logger.debug('key_type: %s' % key_type)
       return jsonify({"key_type": key_type}), 200
   ```

3. **Create `tests/test_dkim_key_type.py`**:

   ```python
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
   ```

---

## Test plan

**Existing tests** — none cover the new endpoint; all existing tests continue to pass unchanged.

**New tests in `tests/test_dkim_key_type.py`**:

| Test | Input | Expected |
|---|---|---|
| `test_returns_200_with_explicit_k_tag` | Record with `k=rsa` | HTTP 200 |
| `test_returns_rsa_for_explicit_k_tag` | Record with `k=rsa` | `{"key_type": "RSA"}` |
| `test_returns_rsa_default_when_k_tag_absent` | Existing fixture (no `k=` tag) | `{"key_type": "RSA"}` |
| `test_returns_400_when_dkim_record_missing` | `{"wrong_field": "value"}` | HTTP 400 |

The first two tests share the same input and could be one test; they are kept separate to mirror the two-test pattern of `test_healthz.py` (status code check distinct from body check).

---

## Risks and open questions

1. **TTL stripping heuristic**: The helper strips a trailing token if `isdigit()` returns true. A `p=` value ending in a space followed by digits (unlikely but possible in malformed input) could be mistakenly stripped. This is acceptable for the service's use case but worth noting.

2. **`k=` tag with uppercase value in the wire format** (e.g., `k=RSA`): The helper lowercases the tag name for matching but returns the value uppercased — this is correct, but execute should verify the `startswith('k=')` match is done on `tag.lower()` not on the raw tag (the plan does this correctly via `tag.lower().startswith('k=')`).

3. **Bare tag-list input** (no `TXT` token): The helper handles this via the `StopIteration` fallback. No test exercises this path — if the operator considers it in-scope, add a fifth test: `record = "v=DKIM1; k=ed25519; p=ABC"` → `{"key_type": "ED25519"}`.

4. **`ed25519` key type**: No test uses a non-RSA type. If the goal's "e.g., RSA" implies multi-type support must be demonstrated, add a test with `k=ed25519` expecting `{"key_type": "ED25519"}`.

5. **Error response shape on 400**: The plan returns `{"error": "missing dkim_record"}`. If the operator prefers a different error envelope, specify before execute runs.
