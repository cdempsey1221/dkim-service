# Design

## Approach

Extract one private helper `_parse_dkim_record(record)` into `dkim.py` that performs the whitespace tokenization and semicolon-delimited tag parsing shared by all three functions. The helper returns a 2-tuple `(tokens, tags)`:

- `tokens`: the `list[str]` from `record.split()` — used by `split_key_by_val` for positional access.
- `tags`: an ordered `list[tuple[str, str]]` of `(key, value)` pairs where `key` is `k.strip().lower()` and `value` is `v.strip()`, derived from `part.partition('=')` on each semicolon-split segment that contains `'='`. — used by `parse_key_type` and `is_valid_dkim`.

Both pieces of data derive from the same initial tokenization pass, so computing them together avoids the redundant `record.split()` calls currently scattered across the three functions. Every caller consumes at least one element of the return value; no dead fields.

Callers unpack with positional syntax: `split_key_by_val` uses `tokens, _ = _parse_dkim_record(key)` (discards tags since it does positional slicing only); `parse_key_type` and `is_valid_dkim` use `_, tags = _parse_dkim_record(record)` (discard tokens since they operate on tag pairs only). Tag pair iteration uses positional unpacking: `for key, value in tags:`.

## Changes by file

- **`dkim.py`** — insert `_parse_dkim_record` helper; rewrite bodies of `split_key_by_val`, `parse_key_type`, and `is_valid_dkim` to call it. No other functions touched.
- **No test files changed.** All existing tests must pass unchanged.

## Step-by-step plan

### Step 1 — Insert `_parse_dkim_record` at line 28

Insert the following function immediately before `split_key_by_val`, which currently starts at line 28. This places the helper above all three callers so it is defined before first use:

```python
def _parse_dkim_record(record):
    tokens = record.split()
    tags = []
    for token in tokens:
        for part in token.split(';'):
            part = part.strip()
            if '=' in part:
                k, _, v = part.partition('=')
                tags.append((k.strip().lower(), v.strip()))
    return tokens, tags
```

Behavioral notes:
- `record.split()` matches exactly the tokenization used by all three current functions.
- The inner loop (`token.split(';')` + `strip()`) matches the semicolon splitting in both `parse_key_type` (line 46) and `is_valid_dkim` (line 55).
- The `'=' in part` guard matches `is_valid_dkim` (line 57). `parse_key_type` checks `tag.lower().startswith('k=')` which implies `=` is present, so this guard excludes the same set of non-tag parts for both callers.
- `k.strip().lower()` matches `is_valid_dkim` line 59.
- `v.strip()` matches `is_valid_dkim` line 59.
- The empty string produced by `token.split(';')` on a trailing semicolon (e.g., `'k=rsa;'` → `['k=rsa', '']`) is stripped to `''`, does not contain `'='`, and is skipped — matching current behavior where `parse_key_type` checks `startswith('k=')` on `''` (no match) and `is_valid_dkim` skips parts without `'='`.
- Pairs are appended in encounter order (whitespace-token order, then semicolon-split order within each token), preserving the first-match semantics `parse_key_type` relies on and the last-write-wins semantics `is_valid_dkim` relies on when it builds its dict.

### Step 2 — Rewrite `split_key_by_val` (currently lines 28–42)

Replace the body of `split_key_by_val` with:

```python
def split_key_by_val(key):
    tokens, _ = _parse_dkim_record(key)
    name = tokens[0]
    content_1 = f"{tokens[1]} {tokens[2]}"
    content_2 = tokens[3]
    content_3 = tokens[4]

    app.logger.debug('name: %s \n content1: %s \n content2: %s\n content3 %s\n' % (name, content_1, content_2, content_3) )

    split_key_json = {'record1': f"{name} {content_1} {content_2}", 'record2': f"{name} TXT {content_3}"}

    app.logger.debug(split_key_json)

    return split_key_json
```

Differences from current code:
- `tokens` replaces five separate `key.split()` calls with one split inside the helper.
- The debug log lines and string formatting are unchanged — same variables logged, same format strings.
- The returned dict keys and f-string templates are identical.
- `IndexError` on fewer than 5 tokens is preserved: `tokens[4]` raises `IndexError` just as `key.split()[4]` does today. The helper itself does not guard token count.
- `tokens, _` discards the tags list since `split_key_by_val` does no tag-level logic. The underscore signals an intentionally unused return value.

### Step 3 — Rewrite `parse_key_type` (currently lines 44–50)

Replace the body of `parse_key_type` with:

```python
def parse_key_type(record):
    _, tags = _parse_dkim_record(record)
    for key, value in tags:
        if key == 'k':
            return value.upper()
    return 'RSA'  # RFC 6376 §3.3 default
```

Differences from current code:
- Replaces manual whitespace → semicolon → `startswith('k=')` scan with iteration over pre-parsed `(key, value)` pairs.
- `key == 'k'` is equivalent to `tag.lower().startswith('k=')` for parts that contain `=`: the helper already normalizes the key to lowercase and strips it, so `'k'` is the only possible normalized form of a `k` tag name. Parts without `=` are excluded by the helper's guard, matching the implicit exclusion in `startswith('k=')`.
- `value.upper()` replaces `tag[2:].strip().upper()`. The helper already strips the value, and `tag[2:]` was the portion after `k=` — which is exactly what `partition('=')` returns as `v`.
- First-match wins: the `for` loop returns on the first pair with `key == 'k'`, matching the current early-return behavior.
- Default `'RSA'` preserved with the same comment.

### Step 4 — Rewrite `is_valid_dkim` (currently lines 52–60)

Replace the body of `is_valid_dkim` with:

```python
def is_valid_dkim(record):
    _, tags = _parse_dkim_record(record)
    tag_map = {}
    for key, value in tags:
        tag_map[key] = value
    return tag_map.get('v', '').upper() == 'DKIM1' and 'p' in tag_map
```

Differences from current code:
- Replaces manual token/semicolon/`partition` loop with iteration over pre-parsed tag pairs.
- `tag_map[key] = value` in encounter order produces last-write-wins semantics, identical to the current `tags[key.strip().lower()] = val.strip()` dict assignment.
- The validation condition is character-for-character the same logic, operating on `tag_map` instead of `tags`.
- `p=` (empty value) still produces `('p', '')` in the pairs, which becomes `'p': ''` in the dict, so `'p' in tag_map` is `True` — matching current revoked-key-is-valid behavior.
- `v=dkim1` (lowercase) still normalizes to `('v', 'dkim1')`, and `tag_map.get('v', '').upper()` produces `'DKIM1'` — matching current case-insensitive check.

### Step 5 — No changes to endpoints or other functions

Lines 62–98 (endpoints, `healthz`, `readyz`, `__main__`) are not modified. They call the three functions by name and will pick up the refactored bodies transparently.

## Test plan

All existing tests pass unchanged — no test modifications:

| Test file | What it covers | Why it still passes |
|---|---|---|
| `tests/test_split_key_by_val.py` | Exact string output of `split_key_by_val` for canonical input | `tokens` come from the same `record.split()`; f-string templates are identical |
| `tests/test_dkim_key_type.py` | `/dkim_key_type` endpoint — explicit `k=rsa`, missing `k`, missing payload | `parse_key_type` returns same values; endpoint unchanged |
| `tests/test_validate_dkim.py` | `/validate_dkim` endpoint — valid, missing `v`, missing `p`, revoked `p=`, missing payload | `is_valid_dkim` produces same boolean; endpoint unchanged |
| `tests/test_healthz.py` | `/healthz` GET | No parsing code touched |
| `tests/test_readyz.py` | `/readyz` GET | No parsing code touched |

No new tests are required. The refactor is purely internal; the behavioral contract is fully covered by existing tests.

## Risks and open questions

- **Whitespace normalization**: The helper uses `record.split()` which matches all three current functions. Any input where `split()` behavior differs from expectations (e.g., non-breaking spaces, tabs) was already handled identically by the current code. No change.

- **Traversal order for duplicate tags**: `parse_key_type` returns the first `k` tag; `is_valid_dkim` uses the last value for any duplicated tag. Both semantics are preserved because the helper returns pairs in encounter order and each caller applies its own strategy (early return vs. dict overwrite). No open question.

- **Logging in `split_key_by_val`**: The two `app.logger.debug` calls log the same intermediate variables (`name`, `content_1`, `content_2`, `content_3`, `split_key_json`) with the same format strings. Log output is identical. Tests do not assert on logs, but operational debugging is unaffected.

- **Exception behavior**: `split_key_by_val` will still raise `IndexError` on inputs with fewer than 5 whitespace tokens because `tokens[4]` indexes into the list returned by the helper's `record.split()`. The helper itself performs no bounds checking. This matches current behavior exactly.

- **No open questions remain**. The helper's return shape is specified (2-tuple of `list[str]` and `list[tuple[str, str]]`), unpacking syntax is specified (positional), and all fields are consumed by at least one caller.
