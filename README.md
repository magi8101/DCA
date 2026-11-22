# DCA

**DCA** is a data compression project exploring two families of algorithms side by side:

- **Lossless** — compression that reproduces the input byte-for-byte on decompression.
- **Lossy** — compression that discards information to reach smaller sizes, trading fidelity for ratio.

The goal is a common interface over both families so implementations can be compared on the same inputs, with the same tooling.

## Status

Early scaffold. The directory layout exists; no implementations have been written yet, so nothing here builds or runs.

## Repository layout

```
.
├── .github/workflows/ci.yml   style checks on every push and pull request
├── .clang-format              Google style, used by CI and editors
├── README.md
└── src/
    ├── Common/                shared code: byte/bit streams, status types
    ├── Lossless/              lossless codecs
    └── Lossy/                 lossy codecs
```

## Coding standards

Code targets **C++20** and follows the **[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)**. The rules below are the parts that matter day to day; consult the upstream guide when a case is not covered.

The guide exists to serve a few goals, in this order — use them to settle anything ambiguous:

1. **Optimize for the reader, not the writer.** Code is read far more than written.
2. **Be consistent.** Naming style should tell the reader what kind of entity a name is without looking up its declaration. Local consistency with existing code outranks personal taste.
3. **Avoid surprising or dangerous constructs**, and avoid anything an average C++ programmer would find hard to maintain. The absence of a prohibition is not a license to be clever.

### Naming

| Entity | Style | Example |
|---|---|---|
| File | lowercase, `_`, extensions `.cc` / `.h` | `http_server_logs.cc` |
| Type (class, struct, enum, alias, concept, type template param) | `PascalCase` | `UrlTable` |
| Function | `PascalCase` | `AddTableEntry()` |
| Accessor / mutator | may be `snake_case` | `count()`, `set_count()` |
| Variable, parameter, struct data member | `snake_case` | `table_name` |
| Class data member | `snake_case_` (trailing underscore) | `table_name_` |
| Constant (`const` / `constexpr`, fixed for program lifetime) | `kPascalCase` | `kDaysInAWeek` |
| Enumerator | `kPascalCase`, not `ALL_CAPS` | `kOutOfMemory` |
| Namespace | `snake_case`, project-unique | `dca` |
| Macro (avoid) | `PROJECT_ALL_CAPS` | `DCA_ROUND` |

Abbreviations count as one word: `StartRpc()`, not `StartRPC()`. No Hungarian notation.

### Formatting

- 80 columns maximum. Exceptions: unsplittable URLs and string literals, includes, header guards, using-declarations.
- 2-space indent, spaces only, never tabs. Wrapped parameters and continuation lines: 4 spaces.
- Opening brace at the end of the line. Braces always on `if` / `for` / `while`; never omit them on `if ... else`.
- `public:` / `protected:` / `private:` are indented one space, in that order.
- Namespace contents are not indented; close with `}  // namespace name`.
- Pointers and references bind to the type: `char* c;`, `const std::string& s;`. Never declare multiple variables where any has `*` or `&`.
- Two spaces before a trailing `//` comment. No trailing whitespace.
- `return expr;` without extra parentheses unless they aid a complex expression.

### Headers and scoping

- Every `.cc` has a matching `.h`, except tests and small `main` files. Headers are self-contained and use `#define` guards named `<PROJECT>_<PATH>_<FILE>_H_` — not `#pragma once`.
- Include order, one blank line between groups and alphabetical within each: related header, C system headers, C++ standard library, other libraries, project headers. Use full paths from the project root; never `.` or `..`.
- Include what you use; do not rely on transitive includes. Avoid forward declarations of things you do not own.
- No `using namespace`, no inline namespaces, and nothing declared in `std`.

### Language features and API rules

These are the rules most often forgotten in review.

- **No exceptions.** Report errors through return values (a `Status`-style type) and treat truly fatal errors as program termination.
- **No implicit conversions.** Mark single-argument constructors and conversion operators `explicit` (copy/move constructors and `initializer_list` constructors are exempt).
- **Make copy and move intent explicit** in every class's public interface: default or delete the operations.
- **Data members are `private`** (constants excepted). Use `struct` only for passive data with all-public fields.
- **Prefer return values over output parameters.** Inputs first, outputs last.
- **Ownership:** a single, fixed owner; transfer with `std::unique_ptr`; shared ownership only with a strong reason, then `std::shared_ptr<const T>`. Never `auto_ptr`.
- **Integers:** `int` for ordinary values, `int64_t` when a value may reach 2^31, and avoid unsigned types except for bit patterns and modular arithmetic. Do not use `unsigned` to mean "never negative".
- **Casts:** C++ casts or brace-init (`int64_t{x}`), never `(int)x`.
- Use **`nullptr`** for pointers and `'\0'` for the null character.
- Prefer **`++i`** over `i++` when the value is unused.
- **`auto`** only when it makes code clearer or safer — not merely shorter.
- **Lambdas:** capture explicitly when the lambda escapes the scope; `[&]` only when its lifetime is clearly shorter than the captures'.
- **Static and global objects** must be trivially destructible. No global `std::string`, `std::map`, or smart pointers; use `constexpr` `string_view` / arrays, or a leaked function-local static pointer.
- **Macros:** avoid. Prefer `constexpr`, `inline`, or enums.
- **`switch`:** include `default` unless switching over an enum, and annotate intentional fall-through with `[[fallthrough]];`.
- **Comments say why, not what.** Document non-obvious APIs: inputs and outputs, nullability, lifetime and ownership, thread-safety.
- **Inclusive language:** avoid "master/slave" and "whitelist/blacklist"; use gender-neutral wording.
- **`long double`:** avoid, it is not portable.

When editing code that does not conform, match the surrounding file rather than mixing two styles in one place, and mention the discrepancy if it is significant.

### Enforcement

- **`.clang-format`** (`BasedOnStyle: Google`) reproduces the formatting rules. Run `clang-format -i <file>` rather than hand-formatting, then review what a formatter cannot judge.
- **cpplint** handles the cheap mechanical checks: line length, tabs, trailing whitespace, `using namespace`, C-style casts, header guards, `NULL`, and similar. It has both false positives and false negatives, so treat it as advice and confirm each hit by reading the code.
- **CI** (`.github/workflows/ci.yml`) installs both tools and runs them on every push and pull request, failing on any finding.

Run the checks locally before pushing:

```sh
pip install cpplint
find src -type f \( -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' \
  -o -name '*.h' -o -name '*.hpp' -o -name '*.hh' \) \
  -exec clang-format --dry-run --Werror {} +
cpplint --recursive --linelength=80 --filter=-legal/copyright src
```

The copyright filter is deliberate: this project does not require per-file copyright headers, so leaving it on would fail every file.

## Planned scope

**Lossless**

- Encoding and decoding that round-trip to the exact original bytes.
- Byte-for-byte round-trip tests as the acceptance criterion for every codec.

**Lossy**

- Encoders with an explicit quality or target-size parameter.
- A defined distortion measure (for example signal-to-noise ratio for media, or edit distance for text) so quality is comparable between codecs, not just asserted.

**Shared**

- A single `compress` / `decompress` entry point per codec, so implementations can be swapped in benchmarks.
- Benchmarks reporting compressed size, ratio, and encode/decode time on a fixed corpus.

## Getting started

The build tooling is still to be chosen, so there is nothing to compile yet. The style checks above run today; CI adds a build and test job once a build system is in place.

## Contributing

Shared machinery belongs in `src/Common/`, not in a codec directory. Add a new codec as its own directory under `src/Lossless/` or `src/Lossy/`, expose the shared `compress` / `decompress` interface, and include round-trip tests alongside the implementation. Contributions are expected to pass the style checks in CI.

## License

Not chosen yet.
