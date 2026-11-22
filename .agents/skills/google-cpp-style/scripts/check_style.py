#!/usr/bin/env python3
"""Mechanical checks for a subset of the Google C++ Style Guide.

Heuristic by design: every finding is a lead to confirm by reading the
code, not a verdict. Strings and comments can false-positive some checks
(casts, NULL, explicit, public members, fall-through).

Usage: check_style.py [--json] FILE [FILE ...]
Exit code: 0 = no findings, 1 = findings, 2 = usage error.
"""
import json
import os
import re
import sys

MAX_LINE = 80

C_CAST = re.compile(
    r"\((?:const\s+)?(?:unsigned\s+|signed\s+)?"
    r"(?:[A-Z][\w:<>]*|int|char|long|short|float|double|void|size_t|"
    r"uint\d+_t|int\d+_t)\s*\*?\s*\)\s*[\w(]"
)
NULL_RE = re.compile(r"\bNULL\b")
USING_NS = re.compile(r"^\s*using\s+namespace\s+([\w:]+)")
PRAGMA_ONCE = re.compile(r"^\s*#\s*pragma\s+once\b")
TODO_BARE = re.compile(r"//\s*TODO(?!\s*\()")
MULTI_DECL = re.compile(r"^\s*(?:int|char|long|float|double|auto)\s+\w+\s*,\s*\w+")
GUARD_IFNDEF = re.compile(r"^\s*#\s*ifndef\s+([A-Z0-9_]+)\s*$")
GUARD_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Z0-9_]+)\s*$")
INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')
CLASS_RE = re.compile(r"^\s*(class|struct)\s+([A-Za-z_]\w*)")
ACCESS_RE = re.compile(r"^\s*(public|protected|private)\s*:")
CASE_RE = re.compile(r"^\s*(case\b.*|default)\s*:\s*$")
TERMINATOR_RE = re.compile(
    r"\b(break|return|throw|continue|goto)\b|\[\[fallthrough\]\]")
MEMBER_RE = re.compile(
    r"^\s*(?:const\s+|static\s+|mutable\s+)*"
    r"[A-Za-z_][\w:<>,\s\*&]*?\s+([A-Za-z_]\w*)\s*(=[^;]*)?;\s*$")


def include_group(inc, paired_base):
    """Guide order: paired header, C, C++ stdlib, other libraries, project."""
    name, quoted = inc
    if quoted and os.path.basename(name) == paired_base:
        return 0
    if not quoted:
        if "/" in name:
            return 3
        if name.endswith(".h"):
            return 1
        return 2
    return 4


def check_includes(path, lines, add):
    paired = ""
    if path.endswith(".cc"):
        paired = os.path.basename(path)[:-3] + ".h"
    max_group = -1
    last_in_group = {}
    for lineno, line in enumerate(lines, 1):
        m = INCLUDE_RE.match(line)
        if not m:
            continue
        inc = (m.group(2), m.group(1) == '"')
        group = include_group(inc, paired)
        if group < max_group:
            add(lineno, f"include <{inc[0]}> is out of the guide's group "
                        "order (paired, C, C++ stdlib, libraries, project)")
        max_group = max(max_group, group)
        prev = last_in_group.get(group)
        if prev and inc[0] < prev:
            add(lineno, f"include <{inc[0]}> breaks alphabetical order "
                        f"within its group (after <{prev}>)")
        last_in_group[group] = inc[0]


def check_classes(path, lines, add):
    """Track class scopes for the explicit and public-member checks."""
    stack = []  # dicts: name, kind, body_depth, access
    depth = 0
    pending = None  # (kind, name) seen, waiting for '{'
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        cm = CLASS_RE.match(line)
        if cm and ("{" in line or stripped.endswith((":", ";")) is False):
            if ";" not in line.split("{")[0] or "{" in line:
                pending = (cm.group(1), cm.group(2))
        am = ACCESS_RE.match(line)
        if am and stack and depth == stack[-1]["body_depth"]:
            stack[-1]["access"] = am.group(1)

        if stack:
            top = stack[-1]
            # Missing explicit: a one-argument constructor without it.
            ctor = re.match(
                r"^\s*(explicit\s+)?~?" + re.escape(top["name"]) +
                r"\s*\(([^)]*)\)", line)
            if ctor and not ctor.group(1) and not stripped.startswith("~"):
                params = ctor.group(2).strip()
                if params and "," not in params:
                    ptype = re.sub(r"\s*[A-Za-z_]\w*\s*$", "", params)
                    ptype = ptype.replace("const", "").replace("&", "").strip()
                    if ptype != top["name"]:
                        add(lineno, f"constructor {top['name']}({params}) can "
                                    "be called with one argument but is not "
                                    "marked explicit")
            # Public data members in a class (structs are exempt).
            if top["kind"] == "class" and top["access"] == "public":
                mm = MEMBER_RE.match(line)
                if (mm and "(" not in line and "using " not in line
                        and "typedef" not in line
                        and "static" not in line and "constexpr" not in line
                        and not re.search(r"\bconst\b.*;", line)):
                    add(lineno, f"public data member '{mm.group(1)}' in class "
                                f"{top['name']} (data members should be "
                                "private; use accessors)")

        opens = line.count("{")
        closes = line.count("}")
        if pending and opens:
            depth_after = depth + opens - closes
            stack.append({"name": pending[1], "kind": pending[0],
                          "body_depth": depth + 1,
                          "access": "private" if pending[0] == "class"
                          else "public"})
            pending = None
            depth = depth_after
        else:
            depth += opens - closes
        while stack and depth < stack[-1]["body_depth"]:
            stack.pop()


def check_switches(path, lines, add):
    """Flag case labels whose block falls through without a terminator."""
    i = 0
    while i < len(lines):
        if not re.search(r"\bswitch\s*\(", lines[i]):
            i += 1
            continue
        # Collect labels until the switch block closes (brace balance).
        depth = 0
        started = False
        labels = []  # (lineno, segment_lines)
        j = i
        while j < len(lines):
            line = lines[j]
            depth += line.count("{") - line.count("}")
            if "{" in line:
                started = True
            lm = CASE_RE.match(line)
            if started and lm:
                labels.append((j + 1, []))
            elif labels:
                labels[-1][1].append(line)
            j += 1
            if started and depth <= 0:
                break
        for lineno, segment in labels:
            body = [s for s in segment
                    if s.strip() and not s.strip().startswith("//")
                    and s.strip() not in ("{", "}")]
            if body and not any(TERMINATOR_RE.search(s) for s in segment):
                add(lineno, "case block appears to fall through (no break, "
                            "return, throw or [[fallthrough]])")
        i = max(j, i + 1)


def check_file(path):
    findings = []

    def add(lineno, msg):
        findings.append({"file": path, "line": lineno, "message": msg})

    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        add(0, f"cannot read file: {exc}")
        return findings

    is_header = path.endswith((".h", ".hh", ".hpp", ".hxx"))

    for lineno, line in enumerate(lines, 1):
        if "\t" in line:
            add(lineno, "tab character (indent with 2 spaces, never tabs)")
        if line != line.rstrip():
            add(lineno, "trailing whitespace")
        if len(line) > MAX_LINE and not (
            "#include" in line or "http://" in line or "https://" in line
        ):
            add(lineno, f"line is {len(line)} chars (limit {MAX_LINE})")
        m = USING_NS.match(line)
        if m:
            sev = "in a header (banned)" if is_header else "(discouraged)"
            add(lineno, f"`using namespace {m.group(1)}` {sev}")
        if C_CAST.search(line) and "static_cast" not in line:
            add(lineno, "possible C-style cast (use a C++ named cast or "
                        "fix the types)")
        if NULL_RE.search(line):
            add(lineno, "NULL (use nullptr for pointers)")
        if TODO_BARE.search(line):
            add(lineno, "bare TODO (format: // TODO(username): description)")
        if MULTI_DECL.search(line) and "(" not in line.split(",")[0]:
            add(lineno, "multiple variables in one declaration (one per line)")
        if PRAGMA_ONCE.match(line):
            add(lineno, "#pragma once (the guide requires #define guards)")

    check_includes(path, lines, add)
    check_classes(path, lines, add)
    check_switches(path, lines, add)

    if is_header:
        guard = None
        for i, line in enumerate(lines[:40]):
            m = GUARD_IFNDEF.match(line)
            if m:
                guard = m.group(1)
                nxt = GUARD_DEFINE.match(lines[i + 1]) if i + 1 < len(lines) else None
                if not nxt or nxt.group(1) != guard:
                    add(i + 1, "header guard #ifndef without matching #define")
                break
        if guard is None:
            add(1, "no #define header guard found (guide requires one)")
        elif not guard.endswith("_H_"):
            add(1, f"header guard {guard} should end in _H_ and be derived "
                   "from the file's full path")

    findings.sort(key=lambda f: (f["line"], f["message"]))
    return findings


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    as_json = "--json" in argv[1:]
    if not args:
        print("usage: check_style.py [--json] FILE [FILE ...]",
              file=sys.stderr)
        return 2
    all_findings = []
    for path in args:
        all_findings.extend(check_file(path))
    if as_json:
        print(json.dumps(all_findings, indent=2))
    else:
        for f in all_findings:
            print(f"{f['file']}:{f['line']}: {f['message']}")
        if all_findings:
            print(f"\n{len(all_findings)} finding(s). Heuristic — confirm "
                  "each by reading the code.", file=sys.stderr)
        else:
            print("No mechanical findings.")
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
