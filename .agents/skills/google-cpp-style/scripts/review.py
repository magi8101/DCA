#!/usr/bin/env python3
"""Run the DCA style layers over a set of C++ files.

Four layers, cheapest first: the bundled heuristic scanner, cpplint with
the same flags CI uses, clang-format in dry-run mode against the
repository's .clang-format, and clang-tidy for translation units when a
CMake compilation database is supplied.

Usage: review.py [--json] [--strict] [--build-dir DIR] FILE [FILE ...]
Exit codes: 0 = no findings, 1 = findings, 2 = usage error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_style  # noqa: E402

MAX_LINE = 80
CPPLINT_FILTER = "-legal/copyright"  # The project requires no headers.
SOURCE_SUFFIXES = (".cc", ".cpp", ".cxx")
HEADER_SUFFIXES = (".h", ".hh", ".hpp", ".hxx")
COMPILE_COMMANDS = "compile_commands.json"


def run(command, timeout=120):
    """Run a command, returning None if it cannot start or times out."""
    try:
        return subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def finding(tool, path, line, message):
    return {"tool": tool, "file": path, "line": line, "message": message}


def from_check_style(files):
    """The heuristic scanner that needs no external tooling."""
    results = []
    for path in files:
        for item in check_style.check_file(path):
            results.append(finding("check_style", item["file"], item["line"],
                                   item["message"]))
    return results


def from_cpplint(files, strict):
    """cpplint with the flags from .github/workflows/ci.yml."""
    findings = []
    notes = []
    executable = shutil.which("cpplint")
    if not executable:
        notes.append("cpplint not installed - skipped (pip install cpplint)")
        return findings, notes
    process = run([executable, "--quiet", f"--linelength={MAX_LINE}",
                   f"--filter={CPPLINT_FILTER}", *files])
    if process is None:
        notes.append("cpplint failed to run - skipped")
        if strict:
            findings.append(finding("cpplint", "", 0,
                                    "cpplint is installed but could not run"))
        return findings, notes
    pattern = re.compile(r"^(.+?):(\d+):\s+(.*?)\s+\[([^\]]+)\]\s*$")
    for line in (process.stdout + process.stderr).splitlines():
        match = pattern.match(line)
        if match:
            findings.append(finding(
                "cpplint", match.group(1), int(match.group(2)),
                f"{match.group(3)} [{match.group(4)}]"))
    return findings, notes


def from_clang_format(files, strict):
    """clang-format --dry-run --Werror against the repo's .clang-format."""
    findings = []
    notes = []
    executable = shutil.which("clang-format")
    if not executable:
        notes.append("clang-format not installed - skipped")
        if strict:
            findings.append(finding(
                "clang-format", "", 0,
                "clang-format is required by CI but not installed"))
        return findings, notes
    diagnostic = re.compile(r"^(.+?):(\d+):(\d+): (?:error|warning): (.*)$")
    for path in files:
        process = run([executable, "--style=file", "--dry-run", "--Werror",
                       path])
        if process is None:
            notes.append(f"clang-format failed to run on {path} - skipped")
            if strict:
                findings.append(finding(
                    "clang-format", path, 0,
                    "clang-format could not run on this file"))
            continue
        matched = False
        for line in process.stderr.splitlines():
            match = diagnostic.match(line)
            if match:
                matched = True
                findings.append(finding("clang-format", match.group(1),
                                        int(match.group(2)),
                                        match.group(4)))
        if process.returncode != 0 and not matched:
            notes.append(f"clang-format could not check {path}")
            if strict:
                findings.append(finding(
                    "clang-format", path, 0,
                    "clang-format could not check this file"))
    return findings, notes


def clang_tidy_command(executable, path, build_dir):
    """Return the clang-tidy command for a translation unit, or None.

    Headers and non-C++ translation units are skipped: headers are covered
    through the translation units that include them, and the scanner plus
    cpplint already handle them cheaply. Without a compilation database
    clang-tidy would guess the compile flags and report false errors, so it
    does not run at all.
    """
    if not path.endswith(SOURCE_SUFFIXES):
        return None
    if path.endswith(HEADER_SUFFIXES):
        return None
    if not build_dir:
        return None
    if not os.path.isfile(os.path.join(build_dir, COMPILE_COMMANDS)):
        return None
    return [executable, "-checks=google-*", "--quiet", "-p", build_dir, path]


def from_clang_tidy(files, build_dir, strict):
    """clang-tidy's google-* checks, only with a compilation database."""
    findings = []
    notes = []
    if not build_dir:
        notes.append("clang-tidy skipped (pass --build-dir with a "
                     f"{COMPILE_COMMANDS})")
        return findings, notes
    if not os.path.isfile(os.path.join(build_dir, COMPILE_COMMANDS)):
        notes.append(f"clang-tidy skipped ({build_dir} has no "
                     f"{COMPILE_COMMANDS})")
        return findings, notes
    executable = shutil.which("clang-tidy")
    if not executable:
        notes.append("clang-tidy not installed - skipped")
        if strict:
            findings.append(finding(
                "clang-tidy", "", 0,
                "clang-tidy was requested but is not installed"))
        return findings, notes

    diagnostic = re.compile(
        r"^(.+?):(\d+):(\d+): (?:warning|error): (.*?)(?:\s+\[[^\]]+\])?$")
    for path in files:
        command = clang_tidy_command(executable, path, build_dir)
        if command is None:
            continue
        process = run(command)
        if process is None:
            notes.append(f"clang-tidy failed to run on {path}")
            if strict:
                findings.append(finding(
                    "clang-tidy", path, 0, "clang-tidy could not run"))
            continue
        output = process.stdout + process.stderr
        if "[clang-diagnostic-error]" in output:
            notes.append(f"clang-tidy could not parse {path}; "
                         "is the build directory current?")
            if strict:
                findings.append(finding(
                    "clang-tidy", path, 0,
                    "clang-tidy could not parse this file"))
            continue
        for line in output.splitlines():
            match = diagnostic.match(line)
            if match:
                findings.append(finding("clang-tidy", match.group(1),
                                        int(match.group(2)),
                                        match.group(4)))
    return findings, notes


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        description="Run the DCA style layers over C++ files.")
    parser.add_argument("--json", action="store_true",
                        help="print findings and notes as JSON")
    parser.add_argument("--strict", action="store_true",
                        help="report installed tools that cannot run as "
                             "findings instead of notes")
    parser.add_argument("--build-dir",
                        help=f"CMake build directory with {COMPILE_COMMANDS}; "
                             "turns on clang-tidy")
    parser.add_argument("files", nargs="+", help="source files to review")
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_arguments(argv)
    files = args.files
    missing = [path for path in files if not os.path.isfile(path)]
    if missing:
        for path in missing:
            print(f"review.py: no such file: {path}", file=sys.stderr)
        return 2

    findings = from_check_style(files)
    notes = []
    for collect in (
            lambda: from_cpplint(files, args.strict),
            lambda: from_clang_format(files, args.strict),
            lambda: from_clang_tidy(files, args.build_dir, args.strict)):
        found, skipped = collect()
        findings.extend(found)
        notes.extend(skipped)

    findings.sort(key=lambda item: (item["file"], item["line"], item["tool"]))
    if args.json:
        print(json.dumps({"findings": findings, "notes": notes}, indent=2))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']}: [{item['tool']}] "
                  f"{item['message']}")
        for note in notes:
            print(f"note: {note}", file=sys.stderr)
        if findings:
            print(f"\n{len(findings)} finding(s) across all layers.",
                  file=sys.stderr)
        else:
            print("No findings from any layer.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
