---
name: google-cpp-style
description: Write and review C++ against the Google C++ Style Guide, adapted for the DCA compression project (composition-only, no exceptions, DCA header guards). Use when writing or reviewing C++ files, when applying naming/formatting/ownership rules, or when running the bundled style checker.
---

# Google C++ Style

Write and review C++ against the Google C++ Style Guide
(https://google.github.io/styleguide/cppguide.html). The guide's own
principles govern everything below: optimize for the reader, be consistent
with existing code, and let every rule pull its weight. Where a project has
its own documented deviations, the project wins — consistency with the
surrounding code beats the guide.

## This project: DCA

The repository this skill is installed in is **DCA**, a C++20 data
compression project. Its `README.md` records the binding standards; the
deviations below are the ones that change how the guide is applied here.
Where the two disagree, `README.md` wins.

- **Composition only.** DCA is written as plain value types plus free
  functions: no inheritance, no virtual functions, no class hierarchies.
  A bit reader or writer is a small aggregate passed to `Status`-returning
  free functions. Where another codebase would reach for polymorphism,
  use static dispatch (`concept`s, templates) or a table of function
  pointers — never a virtual base for codec selection. Read
  `references/composition-over-inheritance.md` Part 2 as binding practice
  for this repo, not as optional guidance.
- **No exceptions.** Errors travel as return values (a `Status`-style
  type); only truly fatal errors terminate the program.
- **Header guards** come from the full path under the project prefix:
  `src/Lossless/bit_reader.h` → `DCA_SRC_LOSSLESS_BIT_READER_H_`.
- **No per-file copyright headers.** CI runs cpplint with
  `-legal/copyright` for this reason; don't add headers the project does
  not require.
- **`.clang-format` lives at the repo root** (Google style, C++20, 80
  columns). Run `clang-format -i` from the root so it is picked up.
- **Layout:** `src/Lossless/`, `src/Lossy/`, and shared helpers (byte and
  bit streams, status types) under `src/Common/`. New codecs get their own
  directory and round-trip tests.
- **Integers:** `int` for ordinary values, `int64_t` past 2^31; unsigned
  only for bit patterns and modular arithmetic.
- **Static and global objects must be trivially destructible.** No global
  `std::string`, containers, or smart pointers.

## Quick reference — the rules people get wrong most

**Naming**
- Files: `lowercase_with_underscores.cc` / `.h`; classes and types:
  `UpperCamelCase`; functions: `UpperCamelCase` (accessors/mutators may use
  snake_case like the variable they wrap); variables: `lowercase_with_underscores`;
  class data members: same plus a trailing underscore (`table_name_`);
  struct data members: no trailing underscore; constants (`const`/`constexpr`
  whose value is fixed at compile time): `kUpperCamelCase`; namespaces:
  `lowercase`, no underscores in project namespaces; enums: type
  `UpperCamelCase`, enumerators `kUpperCamelCase`; macros: `ALL_CAPS_WITH_UNDERSCORES`
  (and avoid macros).
- No Hungarian notation, no abbreviations that aren't obvious to a reader
  outside the project.

**Formatting**
- 80-column limit, 2-space indents, no tabs, spaces after commas, pointer
  stars bind to the variable (`char* c;` — one declaration per line).
- Braces: opening brace on the same line for functions and control blocks;
  `} else {` on one line; always brace, or keep condition and body on one
  line — never a lone unbraced body on the next line without care for
  misleading indentation.
- Access specifiers (`public:` etc.) sit one space back from the class body
  indent. Namespaces do not add an indent level.

**Headers**
- Every header is self-contained and has a `#define` guard named
  `<PROJECT>_<PATH>_<FILE>_H_` from the full path.
- Include order: the header for this `.cc` first, then C headers, C++
  standard library, other libraries, then project headers — alphabetical
  within each group.
- Include what you use; forward-declare only when the guide's trade-off
  favours it (never forward-declare standard library templates).

**Hard bans and near-bans (judgment lives in the references)**
- No C++ exceptions. No RTTI (rare exceptions). No `using namespace`, and
  never in a header. No C-style casts. No `NULL` — use `nullptr`. No
  function-local `static` with a non-trivial destructor; no global objects
  with constructors that do work. No default arguments on virtual functions.
  No implicit conversion operators or single-argument constructors without
  `explicit`. Prefer `std::unique_ptr` to express ownership; raw owning
  pointers are a bug waiting to happen.

## How to review code with this skill

1. **Run the mechanical checker first**, from the repository root:
   `python3 .agents/skills/google-cpp-style/scripts/check_style.py [--json]
   <files...>`. It flags tabs, over-length lines, trailing
   whitespace, missing or mismatched header guards, `using namespace`,
   C-style casts, `NULL`, bare TODOs, multi-variable declarations,
   `#pragma once`, out-of-order includes (group order and alphabetical
   order within a group), single-argument constructors missing `explicit`,
   public data members in a class, and switch cases that fall through
   without a terminator. Treat every hit as a lead, not a verdict —
   confirm by reading the code (strings and comments can false-positive
   the cast and `using` checks).
   For a stronger pass, run
   `python3 .agents/skills/google-cpp-style/scripts/review.py [--json]
   [--build-dir build] [--cuda-path "$CUDA_PATH"] [--cuda-arch sm_75]
   [--cuda-include-dir src] <files...>`. DCA has no CMake build yet, so
   omit `--build-dir` until a compilation database exists. It combines the built-in scanner
   with cpplint, `clang-format --style=file --dry-run`, and clang-tidy's
   `google-*` checks when installed. C++ translation units use the CMake
   compilation database when `--build-dir` is provided. CUDA translation
   units use Clang CUDA mode with the selected toolkit, architecture, and
   include directories. Headers are checked through their translation
   units. Missing optional tools are reported as notes; use `--strict` in
   CI to fail if clang-format or clang-tidy cannot run or parse a file.
   The checker's test suite is `scripts/test_check_style.py`; run it
   after any change to the scripts.
2. **Then review by topic**, loading only the reference file for the topic
   in front of you:
   - names, files, constants → `references/naming.md`
   - layout, whitespace, braces → `references/formatting.md`
   - includes, guards, namespaces, linkage, globals → `references/headers-and-scoping.md`
   - constructors, inheritance, operators, parameters, overloading → `references/classes-and-functions.md`
   - smart pointers, casts, exceptions, `auto`, lambdas, templates,
     integer types, macros → `references/language-features.md`
   - inheritance vs composition, polymorphism strategy, dependency
     injection, factories → `references/composition-over-inheritance.md`
     (Part 1 is the guide's rules; Part 2 is practice beyond the guide and
     is labelled as such; Part 3 is the syntax from Google's Abseil Tips)
   - file/class/function comments, TODOs → `references/comments.md`
3. **Report findings grouped by severity**: rule violations that change
   behaviour or ownership first, then consistency and readability items.
   Name the rule and the fix for each finding; quote the guide's decision,
   not just your taste. Don't report the guide's *pros/cons* reasoning as
   findings.
4. **Respect the exceptions**: existing non-conformant code keeps its local
   style (don't reformat a whole legacy file to fix one line), and Windows
   code follows the guide's Windows exceptions (e.g. `#pragma once` is
   still not preferred, but some naming and include rules bend).

## How to write new code with this skill

Draft the code, then self-check in the same order: run the checker on the
file, re-read for the judgment rules (ownership, implicit conversions,
parameter order — inputs before outputs, declaration order in classes:
public API, then protected, then private, with typedefs/constants first
inside each section), and only then hand it over. State plainly which
checks were run.

## Limits

- The guide defers some choices to projects (e.g. whether accessors use
  snake_case). When the surrounding code has clearly chosen, follow it.
- Some guide rules name Google-internal tools or libraries (Abseil,
  cpplint, protobuf idioms). Outside Google, map them to the standard
  library or the project's equivalent and say that you did.
- The checker is heuristic. It cannot see ownership, API design, comment
  quality, whether a name is clear, or whether a class's copy/move
  declarations are consistent — those stay human/agent review steps
  above. It has no suppression or baseline mechanism; a confirmed false
  positive is resolved by reading the code, not by annotating it.
