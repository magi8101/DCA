# Formatting (Google C++ Style Guide — Formatting)

When in doubt, match clang-format with the Google style
(`clang-format -style=Google`) rather than hand-arguing whitespace. These
are the rules it encodes, plus the ones it cannot.

## Lines and indentation
- Maximum line length: **80 characters**. (Exceptions: a comment with a
  URL, an `#include` line, or a string literal that cannot be split
  without harming readability — and even then, prefer a split.)
- Indent with **2 spaces**. Never tabs for indentation.
- Access specifiers in a class (`public:`, `protected:`, `private:`) are
  indented one space less than the class body (offset −1).
- Namespace contents are **not** indented — a namespace adds no level.
- Preprocessor directives start at column 0 (except inside a function,
  where they may be indented to the surrounding block in rare cases).

## Braces and blocks
- Opening brace goes on the same line as the declaration or condition:
  `if (x) {`, `class Foo {`, `void F() {`.
- `} else {` and `} else if (...) {` stay on one line.
- Short conditionals/loops may omit braces only when the whole statement
  fits on one line (`if (x) return;`). Never write an unbraced body on
  the next line in a way that misleads the eye.
- A function body, class body, or block is never written as
  `{}`-on-one-line except for genuinely empty functions and lambdas where
  the file's style allows it.
- `switch` cases are indented one level; case bodies one more. Braces
  around a case are required only when the case declares variables.

## Declarations and calls
- One variable declaration per line. Pointer/reference symbols bind to
  the variable name: `char* c;`, `const std::string& str;` — never
  `char *c` mixed with `int* a, b;` (the second is a bug magnet).
- Function declarations/definitions: return type on the same line as the
  name when it fits; break parameters one-per-line or grouped, indented 4
  spaces on continuation lines, with the closing paren aligned to the
  arguments.
- Long calls wrap the same way: break after an open paren and align.
- Braced initializer lists format like function calls.
- Constructor initializer lists: break before each colon-led entry or put
  each member on its own line, indented 4.

## Whitespace
- Horizontal: space after commas and semicolons in `for`; spaces around
  binary operators; no spaces around `.`, `->`, `*` in dereference, or
  inside `<...>` of templates and casts (`static_cast<int>(x)`); no space
  between a function name and its `(`.
- No trailing whitespace, ever.
- Vertical: at most one blank line in a row in most places; two blank
  lines between top-level definitions in a `.cc`; don't start or end a
  file/block with a blank line; a blank line before a comment block that
  introduces the next chunk of code is normal.

## Literals and expressions
- Floating-point literals always carry digits on both sides of the point:
  `1.0`, not `1.` or `.5`. Use a suffix when the type matters (`1.0f`).
- Long boolean expressions break before the operators, operators at line
  starts, aligned.
- Return expressions are not wrapped in redundant parentheses:
  `return x;`, not `return (x);`.
- Variable initialization prefers `=` or braced init consistently;
  `Type var(args)` for direct initialization where the file does.
