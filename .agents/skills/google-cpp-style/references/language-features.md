# Language features (Google C++ Style Guide — Other C++ Features)

The guide targets **C++20**. Features newer than the project's standard,
or banned below, are findings even if the compiler accepts them.

## Ownership and pointers
- Ownership is expressed in types: `std::unique_ptr` for exclusive
  ownership, `std::shared_ptr` only when ownership is genuinely shared
  (it's the exception, not the default). A raw pointer or reference means
  **non-owning** — say so in a comment when it isn't obvious.
- Never transfer ownership through a raw pointer in new APIs; never use
  `auto_ptr` (removed anyway) or hand-rolled reference counting.
- `new`/`delete` outside a smart-pointer or container owner is a finding.

## The banned and the bounded
- **Exceptions: not used.** Code must not throw or rely on unwinding;
  error handling is by return values / status objects. (Third-party code
  that throws is contained at the boundary.)
- **RTTI: avoid.** Prefer virtual functions or visitor patterns; using
  `typeid`/`dynamic_cast` to switch behaviour on type is a design smell
  the guide calls out.
- **Casting**: use C++ casts only — `static_cast`, `const_cast` (rare,
  commented), `reinterpret_cast` (rare, commented). **No C-style casts.**
  Prefer avoiding the cast entirely (fix the types).
- **Streams**: `<<` for logging and test output is fine; do not use
  iostreams as a general formatting/parsing API where a clearer option
  exists in the project. No `std::endl` in loops (use `'\n'`; `endl`
  flushes).
- **Preincrement**: prefer `++i` over `i++` for iterators and generic
  code (no need to keep the old value).
- **`const`**: use it everywhere it is true — parameters, locals, member
  functions. `const` goes after the type it qualifies in declarations the
  guide writes (`int const*` appears in its examples), but consistency
  with the file wins; what matters is that constness is expressed.
- **`constexpr`/`constinit`/`consteval`**: use them to move work to
  compile time and to name genuinely constant values; don't sprinkle
  `constexpr` on functions that can never be constant-evaluated.
- **Integer types**: of the built-ins, use `int` for ordinary values.
  Fixed-width types (`int32_t`, `uint64_t`) only where the width is part
  of the contract (serialization, protocols). Don't use unsigned to say
  "non-negative" — use assertions/`int` and check; unsigned arithmetic
  wraparound has bitten too often. (Sizes and counts that come from the
  standard library stay `size_t` at that boundary.)
- **`0` and `nullptr`**: pointers get `nullptr`, never `NULL` or `0`;
  `0` is for numbers.
- **`sizeof`**: prefer `sizeof(varname)` over `sizeof(Type)` so the code
  survives type changes.
- **Macros**: avoid. Where one is unavoidable (include guards are
  `#define`s, not macros in this sense), keep it scoped, name it
  `ALL_CAPS`, and never define a macro that changes language syntax.
  Prefer `constexpr`, inline functions, and templates.

## Deduction, lambdas, templates
- **`auto`** is permitted where it makes code clearer or safer — local
  variables with obvious or unspellable types (iterators, lambdas,
  template-heavy expressions). It is not permitted where it hides the
  type a reader needs (top-level API signatures, arithmetic where width
  matters). Structured bindings follow the same rule: fine when the
  elements are obvious, named types when they aren't.
- **Lambdas**: keep them short; a lambda longer than a few lines or with
  nested lambdas gets a name (a function or a named variable). Capture
  explicitly what is used; default captures (`[&]`, `[=]`) only in the
  shortest lambdas where the file's style allows, and never stored
  beyond the call when capturing by reference.
- **Templates**: prefer simple templates with visible definitions in
  headers; heavy template metaprogramming (long compile times, opaque
  errors) is a finding. C++20 concepts are permitted to constrain
  templates where they clarify requirements — name concepts like types.
- **Designated initializers** are permitted in C++20 form
  (`.field = value`, in declaration order) for aggregate structs.
- **Coroutines and C++20 modules**: the guide treats these cautiously;
  follow the project's stance, defaulting to not introducing them into
  code that doesn't already use them.
- **Nonstandard extensions** (e.g. `__attribute__`, statement
  expressions) are not used in portable code; `#ifdef` platform blocks
  follow the project's existing pattern.
- **Friends**: permitted, declared in the `private:` section; a friend
  is part of the API and gets the same review scrutiny.
- **`noexcept`**: mark functions that genuinely cannot throw (move
  operations, destructors, leaf utilities) — the guide encourages it
  where it is provably true, and forbids lying about it.
- **Aliases**: public type aliases are part of the API and named like
  types; don't alias to hide a standard type's name project-wide.
- **Switch statements**: always have a `default` case (or a comment
  explaining its impossibility); fallthrough must be marked
  `[[fallthrough]]` and commented when non-trivial.
