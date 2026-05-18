# verification

- status: pass
- command: python3 -m pytest
- detected from: python markers (pytest via -m)
- duration: 823ms
- exit code: 0
- timed out: false

## output

============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/xadmin/.local/share/loom/worktrees/01KRY15G5F817GCMJ7YNPD45X6
plugins: anyio-4.13.0, typeguard-4.5.1, hydra-core-1.3.2
collected 6 items

tests/test_dkim_key_type.py ...                                          [ 50%]
tests/test_healthz.py ..                                                 [ 83%]
tests/test_split_key_by_val.py .                                         [100%]

=============================== warnings summary ===============================
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:751
  /home/xadmin/.local/lib/python3.12/site-packages/werkzeug/routing/rules.py:751: DeprecationWarning: ast.Str is deprecated and will be removed in Python 3.14; use ast.Constant instead
    parts = parts or [ast.Str("")]

../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:748: 18 warnings
  /home/xadmin/.local/lib/python3.12/site-packages/werkzeug/routing/rules.py:748: DeprecationWarning: ast.Str is deprecated and will be removed in Python 3.14; use ast.Constant instead
    _convert(elem) if is_dynamic else ast.Str(s=elem)

../../../../../../../usr/lib/python3.12/ast.py:587: 18 warnings
  /usr/lib/python3.12/ast.py:587: DeprecationWarning: Attribute s is deprecated and will be removed in Python 3.14; use value instead
    return Constant(*args, **kwargs)

../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:755: 22 warnings
  /home/xadmin/.local/lib/python3.12/site-packages/werkzeug/routing/rules.py:755: DeprecationWarning: ast.Str is deprecated and will be removed in Python 3.14; use ast.Constant instead
    if isinstance(p, ast.Str) and isinstance(ret[-1], ast.Str):

../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:756: 20 warnings
  /home/xadmin/.local/lib/python3.12/site-packages/werkzeug/routing/rules.py:756: DeprecationWarning: Attribute s is deprecated and will be removed in Python 3.14; use value instead
    ret[-1] = ast.Str(ret[-1].s + p.s)

../../../../lib/python3.12/site-packages/werkzeug/routing/rules.py:756: 10 warnings
  /home/xadmin/.local/lib/python3.12/site-packages/werkzeug/routing/rules.py:756: DeprecationWarning: ast.Str is deprecated and will be removed in Python 3.14; use ast.Constant instead
    ret[-1] = ast.Str(ret[-1].s + p.s)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 6 passed, 97 warnings in 0.17s ========================

