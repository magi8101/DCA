#!/usr/bin/env python3
"""Tests for check_style.py and review.py. Run: python3 test_check_style.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_style  # noqa: E402
import review  # noqa: E402

CHECK = os.path.join(HERE, "check_style.py")
REVIEW = os.path.join(HERE, "review.py")


def findings_for(source, suffix=".cc"):
    with tempfile.NamedTemporaryFile(
            "w", suffix=suffix, delete=False, dir="/tmp") as fh:
        fh.write(source)
        path = fh.name
    try:
        return check_style.check_file(path)
    finally:
        os.unlink(path)


def messages(source, suffix=".cc"):
    return [f["message"] for f in findings_for(source, suffix)]


def has(source, needle, suffix=".cc"):
    return any(needle in m for m in messages(source, suffix))


class TestMechanical(unittest.TestCase):
    def test_tab_flagged(self):
        self.assertTrue(has("int main() {\n\treturn 0;\n}\n", "tab"))

    def test_trailing_whitespace(self):
        self.assertTrue(has("int x;  \n", "trailing whitespace"))

    def test_long_line(self):
        self.assertTrue(has("int " + "x" * 90 + ";\n", "limit 80"))

    def test_long_include_exempt(self):
        src = '#include "some/really/long/path/that/goes/on/and/on/and/on.h"\n'
        self.assertFalse(has(src, "limit 80"))

    def test_using_namespace_in_header_banned(self):
        src = "#ifndef X_Y_H_\n#define X_Y_H_\nusing namespace std;\n#endif\n"
        self.assertTrue(has(src, "banned", ".h"))

    def test_using_namespace_in_cc_discouraged(self):
        self.assertTrue(has("using namespace std;\n", "discouraged"))

    def test_c_cast_flagged(self):
        self.assertTrue(has("int y = (int)3.5;\n", "C-style cast"))

    def test_static_cast_clean(self):
        self.assertFalse(has("int y = static_cast<int>(3.5);\n", "C-style"))

    def test_null_flagged(self):
        self.assertTrue(has("char* p = NULL;\n", "nullptr"))

    def test_nullptr_clean(self):
        self.assertFalse(has("char* p = nullptr;\n", "nullptr"))

    def test_bare_todo(self):
        self.assertTrue(has("// TODO fix this\n", "bare TODO"))

    def test_owned_todo_clean(self):
        self.assertFalse(has("// TODO(magi): fix this\n", "bare TODO"))

    def test_multi_decl(self):
        self.assertTrue(has("int a, b;\n", "multiple variables"))

    def test_pragma_once(self):
        self.assertTrue(has("#pragma once\n", "#pragma once", ".h"))


class TestHeaderGuards(unittest.TestCase):
    def test_missing_guard(self):
        self.assertTrue(has("class Foo {};\n", "no #define header guard", ".h"))

    def test_good_guard(self):
        src = "#ifndef FOO_BAR_H_\n#define FOO_BAR_H_\n#endif  // FOO_BAR_H_\n"
        self.assertFalse(has(src, "guard", ".h"))

    def test_guard_suffix(self):
        src = "#ifndef FOO_BAR\n#define FOO_BAR\n#endif\n"
        self.assertTrue(has(src, "_H_", ".h"))

    def test_mismatched_define(self):
        src = "#ifndef FOO_BAR_H_\n#define OTHER_H_\n#endif\n"
        self.assertTrue(has(src, "without matching", ".h"))


class TestIncludes(unittest.TestCase):
    def test_group_order(self):
        src = '#include "foo.h"\n#include <string>\n'
        self.assertTrue(has(src, "group order"))

    def test_alphabetical_within_group(self):
        src = "#include <vector>\n#include <string>\n"
        self.assertTrue(has(src, "alphabetical"))

    def test_paired_header_first_ok(self):
        src = ('#include "thing.h"\n#include <cstddef>\n'
               '#include <string>\n#include "other.h"\n')
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "thing.cc")
            with open(path, "w") as fh:
                fh.write(src)
            msgs = [f["message"] for f in check_style.check_file(path)]
        self.assertFalse(any("include" in m for m in msgs), msgs)


class TestClasses(unittest.TestCase):
    def test_missing_explicit(self):
        src = "class Foo {\n public:\n  Foo(int x);\n};\n"
        self.assertTrue(has(src, "explicit", ".h"))

    def test_explicit_ok(self):
        src = "class Foo {\n public:\n  explicit Foo(int x);\n};\n"
        self.assertFalse(has(src, "not marked explicit", ".h"))

    def test_copy_ctor_not_flagged(self):
        src = "class Foo {\n public:\n  Foo(const Foo& other);\n};\n"
        self.assertFalse(has(src, "not marked explicit", ".h"))

    def test_two_arg_ctor_not_flagged(self):
        src = "class Foo {\n public:\n  Foo(int x, int y);\n};\n"
        self.assertFalse(has(src, "not marked explicit", ".h"))

    def test_public_data_member(self):
        src = "class Foo {\n public:\n  int count;\n};\n"
        self.assertTrue(has(src, "public data member", ".h"))

    def test_private_member_ok(self):
        src = "class Foo {\n private:\n  int count_;\n};\n"
        self.assertFalse(has(src, "public data member", ".h"))

    def test_struct_member_ok(self):
        src = "struct Foo {\n  int count;\n};\n"
        self.assertFalse(has(src, "public data member", ".h"))

    def test_public_function_not_a_member(self):
        src = "class Foo {\n public:\n  int count() const;\n};\n"
        self.assertFalse(has(src, "public data member", ".h"))


class TestSwitch(unittest.TestCase):
    def test_fallthrough_flagged(self):
        src = ("void F(int x) {\n  switch (x) {\n    case 1:\n"
               "      DoThing();\n    case 2:\n      break;\n  }\n}\n")
        self.assertTrue(has(src, "fall through"))

    def test_break_ok(self):
        src = ("void F(int x) {\n  switch (x) {\n    case 1:\n"
               "      DoThing();\n      break;\n    default:\n"
               "      break;\n  }\n}\n")
        self.assertFalse(has(src, "fall through"))

    def test_marked_fallthrough_ok(self):
        src = ("void F(int x) {\n  switch (x) {\n    case 1:\n"
               "      DoThing();\n      [[fallthrough]];\n    case 2:\n"
               "      break;\n  }\n}\n")
        self.assertFalse(has(src, "fall through"))

    def test_stacked_labels_ok(self):
        src = ("void F(int x) {\n  switch (x) {\n    case 1:\n    case 2:\n"
               "      DoThing();\n      break;\n    default:\n"
               "      break;\n  }\n}\n")
        self.assertFalse(has(src, "fall through"))


class TestCli(unittest.TestCase):
    def test_json_output(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".cc", delete=False, dir="/tmp") as fh:
            fh.write("char* p = NULL;\n")
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, CHECK, "--json", path],
                                  capture_output=True, text=True)
            data = json.loads(proc.stdout)
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(any("nullptr" in d["message"] for d in data))
        finally:
            os.unlink(path)

    def test_clean_file_exit_zero(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".cc", delete=False, dir="/tmp") as fh:
            fh.write("int main() { return 0; }\n")
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, CHECK, path],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
        finally:
            os.unlink(path)

    def test_review_runs_and_reports_layers(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".cc", delete=False, dir="/tmp") as fh:
            fh.write("char* p = NULL;\n")
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, REVIEW, "--json", path],
                                  capture_output=True, text=True)
            data = json.loads(proc.stdout)
            tools = {f["tool"] for f in data["findings"]}
            self.assertIn("check_style", tools)
            self.assertEqual(proc.returncode, 1)
        finally:
            os.unlink(path)


class TestReviewCommands(unittest.TestCase):
    def setUp(self):
        self.build_dir = tempfile.mkdtemp(dir="/tmp")
        with open(os.path.join(self.build_dir, "compile_commands.json"),
                  "w") as fh:
            fh.write("[]\n")

    def tearDown(self):
        shutil.rmtree(self.build_dir)

    def test_cpp_uses_compilation_database(self):
        command = review.clang_tidy_command(
            "clang-tidy", "src/workload.cc", self.build_dir)
        self.assertIn("-p", command)
        self.assertIn(self.build_dir, command)
        self.assertEqual(command[-1], "src/workload.cc")

    def test_no_build_dir_skips_tidy(self):
        self.assertIsNone(
            review.clang_tidy_command("clang-tidy", "src/a.cc", None))

    def test_missing_compilation_database_skips_tidy(self):
        empty = tempfile.mkdtemp(dir="/tmp")
        try:
            self.assertIsNone(
                review.clang_tidy_command("clang-tidy", "src/a.cc", empty))
        finally:
            shutil.rmtree(empty)

    def test_header_is_not_analyzed_directly(self):
        self.assertIsNone(review.clang_tidy_command(
            "clang-tidy", "src/workload.h", self.build_dir))

    def test_non_cpp_file_is_not_analyzed(self):
        self.assertIsNone(review.clang_tidy_command(
            "clang-tidy", "README.md", self.build_dir))


if __name__ == "__main__":
    unittest.main(verbosity=1)
