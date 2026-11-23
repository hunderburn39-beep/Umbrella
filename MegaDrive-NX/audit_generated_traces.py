#!/usr/bin/env python3
"""Audit the patched Nuked-MD md.c before compiling the Switch NRO."""
import re
import sys
from pathlib import Path


def function_body(source, signature):
    """Return a C function body using brace depth, skipping strings/comments."""
    match = re.search(re.escape(signature) + r"\s*\{", source)
    if not match:
        raise ValueError("Missing function definition: " + signature)
    start = match.end()
    depth = 1
    i = start
    mode = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if mode == "code":
            if ch == '"':
                mode = "string"
            elif ch == "'":
                mode = "char"
            elif ch == "/" and nxt == "/":
                mode = "line"
                i += 1
            elif ch == "/" and nxt == "*":
                mode = "block"
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i]
        elif mode in ("string", "char"):
            if ch == "\\":
                i += 1
            elif (mode == "string" and ch == '"') or (mode == "char" and ch == "'"):
                mode = "code"
        elif mode == "line" and ch == "\n":
            mode = "code"
        elif mode == "block" and ch == "*" and nxt == "/":
            mode = "code"
            i += 1
        i += 1
    raise ValueError("Unterminated function: " + signature)


def main(path):
    source = Path(path).read_text()
    errors = []
    signature = "int SDLCALL work_thread(void *data)"
    try:
        worker = function_body(source, signature)
    except ValueError as exc:
        errors.append(str(exc))
        worker = ""
    if worker:
        for operation in ("fopen", "fprintf", "fclose", "fwrite", "fputs"):
            if re.search(r"\b" + operation + r"\s*\(", worker):
                errors.append("Filesystem operation in chip worker: " + operation)
        for token in ("__atomic_store_n(&nx_cpu_trace_ready,1,__ATOMIC_RELEASE)",
                      "__atomic_store_n(&nx_rom_trace_ready,1,__ATOMIC_RELEASE)"):
            if token not in worker:
                errors.append("Missing worker publication: " + token)

    for name in ("nx_trace_flush_main", "nx_rom_trace_flush_main"):
        prototype = "static void " + name + "(void);"
        definition = "static void " + name + "(void)"
        if prototype not in source:
            errors.append("Missing forward declaration: " + name)
        try:
            body = function_body(source, definition)
            if "fopen" not in body:
                errors.append("Main-thread flush has no file output: " + name)
        except ValueError as exc:
            errors.append(str(exc))
        # A prototype is not a call. Require a standalone invocation.
        calls = list(re.finditer(r"(?m)^\s*" + re.escape(name) + r"\s*\(\s*\)\s*;", source))
        if not calls:
            errors.append("Missing main-thread invocation: " + name)
        elif prototype in source and source.index(prototype) > calls[0].start():
            errors.append("Invocation precedes declaration: " + name)

    # A published trace must be immutable while the UI thread flushes it.
    # Check generated C rather than relying on textual patches in port.py.
    cpu_guard = re.search(
        r"if\s*\(\s*!nx_cpu_trace_saved\s*&&\s*nx_cpu_trace_n\s*<\s*64\s*&&",
        worker,
    )
    rom_guard = re.search(
        r"md\.vaddress\s*!=\s*nx_rom_last\s*&&\s*!nx_rom_trace_saved",
        worker,
    )
    if not cpu_guard:
        errors.append("CPU trace writes are not guarded after publication")
    if not rom_guard:
        errors.append("ROM trace writes are not guarded after publication")

    if "mcycles >= 2000000ULL" not in worker:
        errors.append("Missing trace timeout in chip worker")

    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    print("Generated trace audit OK: worker has no filesystem calls and main-thread flushes are wired.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 audit_generated_traces.py build/md.c")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
