# Headers and scoping (Google C++ Style Guide — Header Files, Scoping)

## Header files
- **Self-contained**: every header compiles on its own — it includes or
  forward-declares everything it uses. A `.cc` must be able to include its
  own header first and compile.
- **Header guards**: every header uses `#define` guards (not `#pragma
  once`). The guard name is built from the full path in the project:
  `FOO_BAR_BAZ_H_` for `foo/bar/baz.h`:
  ```cpp
  #ifndef FOO_BAR_BAZ_H_
  #define FOO_BAR_BAZ_H_
  ...
  #endif  // FOO_BAR_BAZ_H_
  ```
- **Include what you use**: if a file uses a symbol, it includes the
  header that defines it — never rely on a transitive include.
- **Forward declarations**: prefer including the header. Forward-declare
  only when it avoids an include cycle or a heavy header, and never
  forward-declare standard library or third-party types whose headers are
  cheap — and never declare standard templates yourself
  (`template <class T> class vector;` is forbidden territory).
- **Inline functions in headers**: only small ones (roughly ≤ 10 lines);
  no loops or switches in an inline body. Prefer defining functions in
  the `.cc`.
- **Include order** (groups separated by blank lines, alphabetical inside
  each group):
  1. The paired header for this `.cc` (`foo.cc` includes `foo.h` first).
  2. C system headers (`<stddef.h>`).
  3. C++ standard library headers (`<string>`, `<vector>`).
  4. Other libraries' headers.
  5. This project's headers.
  Conditional includes go at the end of their group.

## Namespaces
- Put code in a namespace named for the project; `.cc` files may use an
  anonymous namespace or `static` for internals — anonymous namespace is
  preferred for functions and types with internal linkage.
- **Never** `using namespace` in a header. In a `.cc`, `using namespace`
  is discouraged; prefer `using` declarations for individual names, and
  never `using` a standard namespace wholesale in shared code.
- Don't declare anything in `namespace std`. Don't use inline namespaces.
- Namespace-closing comment: `}  // namespace foo` for larger scopes.
- Aliases (`using Bar = ...` for a namespace or type) belong in headers
  only when they are part of the public API; local aliases go inside the
  function or class that uses them.

## Linkage, functions, and variables
- Prefer nonmember or static-member functions to global functions;
  a global function should only take its inputs as parameters, not reach
  for globals.
- **Local variables**: declare them where they are first used, initialized
  at declaration, in the narrowest scope possible. Never hoist declarations
  to the top of the function C-style. A variable used in a loop condition
  is declared in the loop.
- **Static and global variables**:
  - No global or static objects whose constructor does non-trivial work,
    and **no function-local statics with non-trivial destructors**
    (destruction order is undefined across translation units). Prefer a
    heap-allocated singleton accessed through a function
    (`static Foo* foo = new Foo();` inside an accessor, never deleted).
  - Class statics that are `constexpr` are fine; dynamically initialized
    statics are a review flag.
  - `thread_local` only for values that are genuinely per-thread state
    and cheap to reason about; treat it like a global in review.
