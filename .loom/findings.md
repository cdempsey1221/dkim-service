# Findings

## Goal restated

Add a `GET /readyz` endpoint to the Flask application that returns HTTP 200 with the JSON body `{"status": "ready"}`, and add a passing test for it.

## Relevant code locations

- `dkim.py` — The Flask application; defines all route handlers (`/split_by_value`, `/healthz`) and the `split_key_by_val` helper
- `tests/test_healthz.py` — Test class for the `/healthz` endpoint; the direct template for the new `/readyz` test
- `tests/test_split_key_by_val.py` — Test for the helper function; secondary reference for test style
- `requirements.txt` — Pinned dependencies (Flask 2.2.3, Werkzeug 2.2.3, no test framework listed — `unittest` from stdlib is used)
- `gunicorn_config.py` — Production server config; no routing logic
- `Dockerfile` — Container definition; exposes port 5000, sets `FLASK_APP=dkim.py`

## Current behaviour

`dkim.py` registers two routes on the `app` Flask instance:

1. `POST /split_by_value` — parses a JSON body with `dkim_record`, calls `split_key_by_val()`, returns a two-record JSON object.
2. `GET /healthz` — returns `jsonify({"status": "ok"}), 200`. This is the direct analogue for the new endpoint.

Tests use Python `unittest` with Flask's built-in test client:

```python
self.client = app.test_client()
response = self.client.get('/healthz')
self.assertEqual(response.status_code, 200)
body = json.loads(response.data)
self.assertEqual(body, {"status": "ok"})
```

There is no `pytest` or other test runner configuration; tests are plain `unittest.TestCase` subclasses importable via `python -m unittest discover`.

## Constraints and assumptions

- **Framework**: Flask 2.2.3 (pinned). Use `@app.route` decorator and `jsonify` — consistent with existing routes.
- **Return convention**: Route handlers return `jsonify({...}), <status_code>`. The `/healthz` handler returns an explicit `200`; the new endpoint should do the same for parity.
- **JSON body**: Must be exactly `{"status": "ready"}` — the goal specifies the string `"ready"` (vs `"ok"` used by `/healthz`).
- **Test file placement**: All tests live in `tests/`. The new test file should follow the naming pattern `tests/test_readyz.py` (matching `test_healthz.py`).
- **Test imports**: Tests import directly from `dkim` (not a package path), so the test runner must be invoked from the repo root. No `__init__.py` files exist under `tests/`.
- **Test class structure**: One `TestCase` subclass per file, `setUp` creates `app.test_client()`, individual `test_*` methods assert status code and JSON body separately (two tests in `test_healthz.py`).
- **No logging**: The `/healthz` handler has no `app.logger` calls; the new endpoint should match that minimal style.
- **HTTP method**: `GET` only — consistent with `/healthz` which also restricts to `methods=['GET']`.

## Risks and open questions

- **Test discovery**: There is no `pytest.ini`, `setup.cfg`, or `tox.ini`. It is unclear how tests are currently run in CI (if any). The design phase should ensure the new test file is discoverable by whatever runner is in use. `python -m unittest discover tests` will find it if named `test_readyz.py`.
- **Naming ambiguity — `readyz` vs `ready`**: Kubernetes convention uses `/readyz` (with z); the goal spec uses that spelling. No risk of collision with existing routes.
- **Single vs. two test methods**: `test_healthz.py` uses two separate test methods (one for status code, one for body). The design phase should decide whether to mirror that exactly or consolidate — mirroring is the safer, most consistent choice.
- **gunicorn vs flask run**: The `Dockerfile` uses `flask run`, not gunicorn, despite `gunicorn_config.py` existing. This is irrelevant to the endpoint change but worth noting — the new route will be served correctly either way.
- **No authentication/middleware**: No auth, rate-limiting, or middleware is applied to any route. The new endpoint needs none.
