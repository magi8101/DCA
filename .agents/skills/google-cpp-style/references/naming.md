# Naming (Google C++ Style Guide — Naming)

General principle: a name tells what a thing is or does, not how it works.
Give names the length the scope deserves — a loop index in a 3-line loop
can be short; a global cannot. No encoding of type information into names
(no Hungarian notation, no `strName`, no `iCount`). Avoid abbreviations
unless they are obvious to a reader outside the project or standard in the
domain; never abbreviate by deleting letters (`fn` for function is fine in
a tiny scope, `CalcTot` is not).

## Files
- All lowercase, underscores between words: `my_useful_class.cc`,
  `my_useful_class.h`, `my_useful_class_test.cc`.
- `.h` for headers, `.cc` for sources (not `.cpp`).
- Names should mirror the main class in the file (`foo.h` defines `Foo`).

## Types (classes, structs, enums, typedefs, using aliases, concepts)
- `UpperCamelCase` (CapWords), no underscores: `UrlTable`, `UrlTableTester`.
- Type aliases follow the same rule: `using PropertiesMap = ...;`

## Variables
- Ordinary variables and parameters: `lowercase_with_underscores`:
  `table_name`, `num_entries`.
- Class data members: same, plus a trailing underscore: `table_name_`,
  `num_entries_`. (This is how readers distinguish members at a glance.)
- Struct data members: plain `lowercase_with_underscores`, **no** trailing
  underscore — structs are passive data.
- Globals: prefix with `g_` only if the project does so consistently; the
  guide discourages globals in general (see headers-and-scoping.md).

## Constants
- Variables declared `const` or `constexpr` whose value is fixed at
  compile time: `k` + `UpperCamelCase`: `kDaysInAWeek`, `kAndroid8_0_0`.
- Run-time constants (e.g. a `const` local computed from input) are named
  like ordinary variables.

## Functions
- `UpperCamelCase`: `AddTableEntry()`, `DeleteUrl()`, `OpenFileOrDie()`.
- Accessors and mutators may instead match the variable they wrap:
  `table_name()` / `set_table_name(...)`. Pick one convention per class.
- Names should say what the function does; a function returning a value is
  named for that value (`NumEntries()`), a command is a verb phrase.

## Namespaces
- All lowercase, based on the project name; avoid underscores and avoid
  colliding with top-level type names. Project namespaces are short:
  `namespace my_project {`.

## Enumerations
- Enum type: `UpperCamelCase` like other types.
- Enumerators: `kUpperCamelCase` like constants: `kOk`, `kOutOfMemory`.
  (The older `ALL_CAPS` enumerator style is legacy; new code uses `k` style.)
- Prefer `enum class` where the enumerators don't need to leak.

## Templates and macros
- Template parameters: `UpperCamelCase`, short and descriptive
  (`typename T`, `typename InputIterator`); the guide also permits a
  trailing descriptor, e.g. `typename TEnable` — follow the file.
- Macros: `ALL_CAPS_WITH_UNDERSCORES`, and the strong preference is to not
  write a macro at all (see language-features.md).

## Exceptions to the rules
- Names that mirror an existing library or standard API may match that
  API's style (e.g. `begin()`, `end()`, `size()` on a container-like type).
- Test code and test fixtures follow the same rules; test names in
  `TEST()` are `UpperCamelCase` suite and case names.
