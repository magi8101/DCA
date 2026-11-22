#!/usr/bin/env python3
"""Run style checks and optional C++/CUDA tooling for project files.

Use --build-dir to give clang-tidy the CMake compilation database for C++
translation units. CUDA translation units are analyzed with explicit Clang
CUDA flags because CMake records NVCC-specific arguments for those files.

Usage: review.py [options] FILE [FILE ...]
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


def run(command, timeout=120):
    try:
        return subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def find_cuda_path(explicit_path):
    candidates = [
        explicit_path,
        os.environ.get("CUDA_PATH"),
        os.environ.get("CUDA_HOME"),
        "/usr/local/cuda",
        "/usr/lib/cuda",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(
                os.path.join(candidate, "include", "cuda.h")):
            return os.path.abspath(candidate)
    return None


def clang_tidy_command(executable, path, build_dir, cuda_path, cuda_arch,
                       cuda_include_dirs):
    extension = os.path.splitext(path)[1]
    command = [executable, "-checks=google-*", "--quiet"]
    if extension == ".cu":
        if not cuda_path:
            return None
        command.append(path)
        command.extend([
            "--",
            "-x",
            "cuda",
            "-std=c++17",
            f"--cuda-path={cuda_path}",
            f"--cuda-gpu-arch={cuda_arch}",
        ])
        for include_dir in cuda_include_dirs:
            command.extend(["-I", os.path.abspath(include_dir)])
        return command

    if extension in (".h", ".hh", ".hpp", ".hxx"):
        return None
    if build_dir:
        command.extend(["-p", build_dir])
        command.append(path)
        return command
    command.extend([path, "--", "-std=c++17"])
    return command


def add_tool_failure(findings, tool, message, strict):
    if strict:
        findings.append({"tool": tool, "file": "", "line": 0,
                         "message": message})


def from_cpplint(files, strict):
    findings = []
    notes = []
    executable = shutil.which("cpplint")
    if not executable:
        notes.append("cpplint not installed — skipped (pip install cpplint)")
        return findings, notes
    process = run([executable, "--quiet", *files])
    if process is None:
        notes.append("cpplint failed to run — skipped")
        add_tool_failure(findings, "cpplint", "cpplint failed to run", strict)
        return findings, notes
    pattern = re.compile(r"^(.+?):(\d+):\s+(.*?)\s*\[([^\]]+)\]")
    for line in (process.stdout + process.stderr).splitlines():
        match = pattern.match(line)
        if match:
            findings.append({"tool": "cpplint", "file": match.group(1),
                             "line": int(match.group(2)),
                             "message": f"{match.group(3)} [{match.group(4)}]"})
    return findings, notes


def from_clang_format(files, strict):
    findings = []
    notes = []
    executable = shutil.which("clang-format")
    if not executable:
        notes.append("clang-format not installed — skipped")
        add_tool_failure(findings, "clang-format",
                         "clang-format is required but not installed", strict)
        return findings, notes
    for path in files:
        process = run([executable, "--style=file", "--dry-run", "--Werror",
                       path])
        if process is None:
            notes.append(f"clang-format failed to run on {path} — skipped")
            add_tool_failure(findings, "clang-format",
                             f"clang-format failed to run on {path}", strict)
            continue
        pattern = re.compile(r"^(.+?):(\d+):(\d+): error: (.*)$")
        found_diagnostic = False
        for line in process.stderr.splitlines():
            match = pattern.match(line)
            if match:
                found_diagnostic = True
                findings.append({"tool": "clang-format",
                                 "file": match.group(1),
                                 "line": int(match.group(2)),
                                 "message": match.group(4)})
        if process.returncode != 0 and not found_diagnostic:
            notes.append(f"clang-format could not check {path}")
            add_tool_failure(findings, "clang-format",
                             f"clang-format could not check {path}", strict)
    return findings, notes


def from_clang_tidy(files, build_dir, cuda_path, cuda_arch,
                    cuda_include_dirs, strict):
    findings = []
    notes = []
    executable = shutil.which("clang-tidy")
    if not executable:
        notes.append("clang-tidy not installed — skipped")
        add_tool_failure(findings, "clang-tidy",
                         "clang-tidy is required but not installed", strict)
        return findings, notes

    for path in files:
        command = clang_tidy_command(
            executable, path, build_dir, cuda_path, cuda_arch,
            cuda_include_dirs)
        if command is None:
            if path.endswith(".cu"):
                message = f"CUDA toolkit not found; cannot analyze {path}"
                notes.append(message)
                add_tool_failure(findings, "clang-tidy", message, strict)
            continue

        process = run(command)
        if process is None:
            message = f"clang-tidy failed to run on {path}"
            notes.append(message)
            add_tool_failure(findings, "clang-tidy", message, strict)
            continue

        output = process.stdout + process.stderr
        parse_error = (process.returncode != 0 or
                       "[clang-diagnostic-error]" in output)
        if parse_error:
            message = f"clang-tidy could not parse {path} with its build flags"
            notes.append(message)
            add_tool_failure(findings, "clang-tidy", message, strict)
            continue

        pattern = re.compile(r"^(.+?):(\d+):(\d+): (warning|error): (.*)$")
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                findings.append({"tool": "clang-tidy",
                                 "file": match.group(1),
                                 "line": int(match.group(2)),
                                 "message": match.group(5)})
    return findings, notes


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true",
                        help="print findings and notes as JSON")
    parser.add_argument("--build-dir",
                        help="CMake build directory with compile_commands.json")
    parser.add_argument("--cuda-path",
                        help="CUDA Toolkit root; auto-detected when omitted")
    parser.add_argument("--cuda-arch", default="sm_75",
                        help="CUDA architecture for clang-tidy (default: sm_75)")
    parser.add_argument("--cuda-include-dir", action="append", default=[],
                        help="extra CUDA source include directory; repeatable")
    parser.add_argument("--strict", action="store_true",
                        help="fail if installed required linters cannot run")
    parser.add_argument("files", nargs="+", help="source files to review")
    return parser.parse_args(argv[1:])


def main(argv):
    args = parse_arguments(argv)
    files = args.files
    findings = []
    notes = []
    cuda_path = find_cuda_path(args.cuda_path)

    for path in files:
        for item in check_style.check_file(path):
            findings.append({"tool": "check_style", **item})

    found, skipped = from_cpplint(files, args.strict)
    findings.extend(found)
    notes.extend(skipped)

    found, skipped = from_clang_format(files, args.strict)
    findings.extend(found)
    notes.extend(skipped)
    found, skipped = from_clang_tidy(
        files, args.build_dir, cuda_path, args.cuda_arch,
        args.cuda_include_dir, args.strict)
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
