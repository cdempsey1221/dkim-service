# Design

## Approach

Add a `GET /readyz` route to `dkim.py` that returns `jsonify({"status": "ready"}), 200`, mirroring the existing `/healthz` handler exactly except for the path and status string. Add a new test file `tests/test_readyz.py` that mirrors the structure of `tests/test_healthz.py` with two test methods: one asserting HTTP 200, one asserting the JSON body equals `{"status": "ready"}`.

## Changes by file

- `dkim.py` — add a `GET /readyz` route handler returning `jsonify({"status": "ready"}), 200`
- `tests/test_readyz.py` — create new test file with a `TestCase` subclass covering status code and response body

## Step-by-step plan

1. Open `dkim.py` and locate the `/healthz` route handler (the reference implementation).
2. Immediately after the `/healthz` handler, insert a new route:
   ```python
   @app.route('/readyz', methods=['GET'])
   def readyz():
       return jsonify({"status": "ready"}), 200
   ```
   No imports need to change — `jsonify` is already imported via `from flask import Flask, request, jsonify` (or equivalent).
3. Create `tests/test_readyz.py` with the following content, modelled directly on `tests/test_healthz.py`:
   ```python
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
   ```
4. Verify the test is discoverable: `python -m unittest discover tests` from the repo root will find any `test_*.py` file, so `test_readyz.py` qualifies automatically.

## Test plan

- **Existing tests**: `tests/test_healthz.py` and `tests/test_split_key_by_val.py` must continue to pass unchanged — the new route does not touch any existing handler.
- **New tests in `tests/test_readyz.py`**:
  - `test_status_code` — GET `/readyz` returns HTTP 200
  - `test_response_body` — GET `/readyz` returns JSON body exactly equal to `{"status": "ready"}`
- Run all tests with `python -m unittest discover tests` from the repo root to confirm nothing regresses.

## Risks and open questions

- **Flask import line**: The execute phase must confirm the exact existing import line in `dkim.py` (e.g., `from flask import Flask, request, jsonify`) to ensure `jsonify` is already imported and no import change is needed. If `jsonify` is not imported, add it.
- **Placement of new route**: Inserting after `/healthz` is the most logical location; the execute phase should confirm the end of the `/healthz` handler to find the exact insertion point without disrupting surrounding code.
- **No `__init__.py` in `tests/`**: Confirmed by findings — do not add one; it is not needed and could break relative imports elsewhere.
- **CI runner**: The findings note no `pytest.ini` or CI config is visible. The `if __name__ == '__main__': unittest.main()` guard in the new file is harmless but not required; it is included for consistency with potential future direct invocation.
