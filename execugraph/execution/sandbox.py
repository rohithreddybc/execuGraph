"""Subprocess-isolated sandbox for executing LLM-generated Python.

Generated code is sent to a freshly spawned Python interpreter via stdin.
The child enforces a wall-clock timeout, a curated ``__builtins__``, an
import policy, a sanitized environment, and (on POSIX) an address-space
ceiling. Communication is JSON over stdout.

This is *not* a kernel-level container. It is intended to keep the
Evaluator's loop honest and to prevent accidental filesystem / network
damage during long unsupervised experiment runs; it is not a defence
against a determined adversary. See the Limitations section of the paper.

Import policy
-------------
The naive approach -- gate ``__import__`` against a flat allow-list -- is
wrong, because importing an allowed pure-Python module transitively
imports its private C accelerator (``bisect`` pulls ``_bisect``,
``heapq`` pulls ``_heapq``, ``io`` pulls ``_io``). Gating on those roots
rejects correct programs and silently scores them as sandbox violations.

Instead the child (1) pre-imports every allow-listed module *before*
installing the guard, so accelerators land in ``sys.modules`` naturally,
then (2) admits any import whose root is allow-listed or already loaded,
except roots on an explicit deny-list, which are refused unconditionally.
``sys`` and ``io`` are additionally replaced with restricted shims,
because the real modules expose ``sys.modules`` (module-graph escape) and
``io.open`` (filesystem write) respectively.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass

# Modules the child interpreter may import. Private C accelerators reached
# transitively from these are admitted automatically (see module docstring).
_ALLOWED_MODULES = frozenset(
    {
        "math",
        "collections",
        "heapq",
        "bisect",
        "functools",
        "itertools",
        "operator",
        "random",
        "re",
        "string",
        "typing",
        "dataclasses",
        "fractions",
        "decimal",
        "statistics",
        "numbers",
        "copy",
        "json",
        "array",
        "enum",
        "abc",
        # Needed for APPS-style stdin/stdout problems. Both are served to
        # user code as restricted shims, not the real modules.
        "sys",
        "io",
    }
)

# Refused unconditionally, even if pulled into ``sys.modules`` transitively
# by an allow-listed module (``random`` imports ``os`` for ``urandom``).
_DENIED_MODULES = frozenset(
    {
        "os",
        "subprocess",
        "socket",
        "shutil",
        "ctypes",
        "importlib",
        "imp",
        "pickle",
        "marshal",
        "shelve",
        "multiprocessing",
        "threading",
        "_thread",
        "signal",
        "resource",
        "pty",
        "tempfile",
        "pathlib",
        "glob",
        "fileinput",
        "linecache",
        "webbrowser",
        "urllib",
        "http",
        "ftplib",
        "smtplib",
        "telnetlib",
        "ssl",
        "asyncio",
        "sysconfig",
        "platform",
        "site",
        "code",
        "codeop",
        "runpy",
        "gc",
        "inspect",
        "traceback",
        "atexit",
        "builtins",
    }
)

# Address-space ceiling applied per child on POSIX. Not enforceable on
# Windows, where CPython ships no ``resource`` module; the child degrades
# gracefully and the paper reports this platform caveat explicitly.
_MEMORY_LIMIT_BYTES = 1 * 1024 * 1024 * 1024  # 1 GiB


@dataclass
class SandboxResult:
    ok: bool
    stdout: str
    stderr: str
    # one of: none, syntax, runtime, timeout, sandbox_violation, harness_error
    error_class: str
    return_value: object = None


_CHILD_PROGRAM = textwrap.dedent(
    '''
    import sys as _sys, json, builtins, traceback, io as _io_real, contextlib, types

    _ALLOWED = set({allowed!r})
    _DENIED = set({denied!r})
    _MEM_LIMIT = {mem_limit!r}
    _real_import = builtins.__import__

    # --- address-space ceiling (POSIX only) --------------------------------
    try:
        import resource as _resource
        _resource.setrlimit(_resource.RLIMIT_AS, (_MEM_LIMIT, _MEM_LIMIT))
        _MEM_ENFORCED = True
    except Exception:
        _MEM_ENFORCED = False  # Windows: no resource module

    # --- pre-import allow-listed modules so C accelerators load cleanly ----
    for _m in sorted(_ALLOWED):
        try:
            _real_import(_m)
        except Exception:
            pass
    _PRELOADED = set(_sys.modules)

    # --- restricted shims for sys and io ----------------------------------
    # Real sys exposes sys.modules, which reaches any loaded module (os).
    # The standard streams must still resolve to the *real* module objects:
    # APPS-style drivers redirect stdout by assigning sys.stdout, and print()
    # writes to the real sys.stdout, so those three names are proxied through.
    class _SysShim(types.ModuleType):
        _FORWARD = ("stdin", "stdout", "stderr")

        def __getattr__(self, name):
            if name in _SysShim._FORWARD:
                return getattr(_sys, name)
            raise AttributeError("module 'sys' has no attribute " + repr(name))

        def __setattr__(self, name, value):
            if name in _SysShim._FORWARD:
                setattr(_sys, name, value)
            else:
                object.__setattr__(self, name, value)

    _sys_shim = _SysShim("sys")
    _sys_shim.argv = [""]
    _sys_shim.maxsize = _sys.maxsize
    _sys_shim.version_info = _sys.version_info
    _sys_shim.float_info = _sys.float_info
    _sys_shim.setrecursionlimit = _sys.setrecursionlimit
    _sys_shim.getrecursionlimit = _sys.getrecursionlimit
    _sys_shim.exit = _sys.exit
    _sys_shim.intern = _sys.intern

    # Real io exposes io.open, which is builtins.open under another name.
    _io_shim = types.ModuleType("io")
    _io_shim.StringIO = _io_real.StringIO
    _io_shim.BytesIO = _io_real.BytesIO
    _io_shim.IOBase = _io_real.IOBase

    _SHIMS = {{"sys": _sys_shim, "io": _io_shim}}

    def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split('.')[0]
        if root in _DENIED:
            raise ImportError("sandbox: import of '" + root + "' is not permitted")
        if root in _SHIMS:
            return _SHIMS[root]
        if root not in _ALLOWED and root not in _PRELOADED:
            raise ImportError("sandbox: import of '" + root + "' is not permitted")
        return _real_import(name, globals, locals, fromlist, level)

    builtins.__import__ = _guarded_import
    # ``input`` is retained: it reads from sys.stdin, which the harness
    # redirects to an in-memory buffer for APPS-style stdin/stdout problems.
    # Deleting it cannot improve isolation (it reaches no external resource)
    # and systematically fails every stdin-driven candidate.
    for _name in ("open", "breakpoint", "exit", "quit", "help"):
        if hasattr(builtins, _name):
            try:
                delattr(builtins, _name)
            except Exception:
                pass

    payload = json.loads(_sys.stdin.read())
    user_code = payload["code"]
    user_call = payload.get("call")
    stdin_data = payload.get("stdin")
    if stdin_data is not None:
        _sys_shim.stdin = _io_real.StringIO(stdin_data)

    ns = {{"__name__": "__sandbox__"}}
    out = _io_real.StringIO()
    err = _io_real.StringIO()
    result = {{
        "ok": False, "stdout": "", "stderr": "",
        "error_class": "none", "return_value": None,
        "mem_limit_enforced": _MEM_ENFORCED,
    }}
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exec(compile(user_code, "<sandbox>", "exec"), ns, ns)
            if user_call is not None:
                rv = eval(user_call, ns, ns)
                try:
                    json.dumps(rv)
                    result["return_value"] = rv
                except TypeError:
                    result["return_value"] = repr(rv)
        result["ok"] = True
    except SyntaxError as e:
        result["error_class"] = "syntax"
        result["stderr"] = "{{}}: {{}}".format(type(e).__name__, e)
    except ImportError as e:
        msg = str(e)
        result["error_class"] = "sandbox_violation" if "sandbox:" in msg else "runtime"
        result["stderr"] = msg
    except MemoryError as e:
        result["error_class"] = "sandbox_violation"
        result["stderr"] = "sandbox: memory limit exceeded ({{}})".format(e)
    except BaseException as e:
        result["error_class"] = "runtime"
        result["stderr"] = "{{}}: {{}}\\n{{}}".format(
            type(e).__name__, e, traceback.format_exc(limit=4)
        )
    result["stdout"] = out.getvalue()
    if not result["stderr"]:
        result["stderr"] = err.getvalue()
    _sys.stdout.write(json.dumps(result, default=str))
    '''
).strip()


def _child_env() -> dict[str, str]:
    """Minimal environment for the child.

    The parent's environment is *not* inherited: experiment runs carry
    provider credentials (e.g. ``HF_TOKEN``) that generated code must not
    be able to read. Only the variables CPython needs to start are kept.
    """
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": "0"}
    if sys.platform == "win32":
        # Windows requires SYSTEMROOT for socket/crypto init at interpreter start.
        for key in ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "PATHEXT"):
            if key in os.environ:
                env[key] = os.environ[key]
    return env


def run_in_sandbox(
    code: str,
    *,
    call: str | None = None,
    stdin: str | None = None,
    timeout_s: float = 5.0,
    allowed_modules: frozenset[str] = _ALLOWED_MODULES,
    denied_modules: frozenset[str] = _DENIED_MODULES,
    memory_limit_bytes: int = _MEMORY_LIMIT_BYTES,
) -> SandboxResult:
    """Run ``code`` in a child interpreter, optionally evaluating ``call``."""
    program = _CHILD_PROGRAM.format(
        allowed=tuple(sorted(allowed_modules)),
        denied=tuple(sorted(denied_modules)),
        mem_limit=memory_limit_bytes,
    )
    payload = json.dumps({"code": code, "call": call, "stdin": stdin})
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-S", "-c", program],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=_child_env(),
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(
            ok=False, stdout="", stderr="timeout", error_class="timeout"
        )
    stdout = proc.stdout.strip()
    if not stdout:
        return SandboxResult(
            ok=False,
            stdout="",
            stderr=proc.stderr or "child produced no output",
            error_class="harness_error",
        )
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return SandboxResult(
            ok=False, stdout=stdout, stderr=proc.stderr, error_class="harness_error"
        )
    return SandboxResult(
        ok=bool(data.get("ok")),
        stdout=data.get("stdout", ""),
        stderr=data.get("stderr", ""),
        error_class=data.get("error_class", "runtime"),
        return_value=data.get("return_value"),
    )
