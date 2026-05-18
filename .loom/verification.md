# verification

- status: fail
- command: pytest
- detected from: python markers (pytest)
- duration: 805ms
- exit code: 2
- timed out: false

## output

============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/xadmin/.local/share/loom/worktrees/01KRY0N1617YGBZEATYFYNTKPZ
plugins: anyio-4.13.0, typeguard-4.5.1, hydra-core-1.3.2
collected 0 items / 3 errors

==================================== ERRORS ====================================
_________________ ERROR collecting tests/test_dkim_key_type.py _________________
ImportError while importing test module '/home/xadmin/.local/share/loom/worktrees/01KRY0N1617YGBZEATYFYNTKPZ/tests/test_dkim_key_type.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_dkim_key_type.py:3: in <module>
    from dkim import app
E   ModuleNotFoundError: No module named 'dkim'
____________________ ERROR collecting tests/test_healthz.py ____________________
ImportError while importing test module '/home/xadmin/.local/share/loom/worktrees/01KRY0N1617YGBZEATYFYNTKPZ/tests/test_healthz.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_healthz.py:3: in <module>
    from dkim import app
E   ModuleNotFoundError: No module named 'dkim'
_______________ ERROR collecting tests/test_split_key_by_val.py ________________
ImportError while importing test module '/home/xadmin/.local/share/loom/worktrees/01KRY0N1617YGBZEATYFYNTKPZ/tests/test_split_key_by_val.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_split_key_by_val.py:2: in <module>
    from dkim import split_key_by_val
E   ModuleNotFoundError: No module named 'dkim'
=========================== short test summary info ============================
ERROR tests/test_dkim_key_type.py
ERROR tests/test_healthz.py
ERROR tests/test_split_key_by_val.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.15s ===============================

