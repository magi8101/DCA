# Classes and functions (Google C++ Style Guide — Classes, Functions)

## Constructors and class design
- Constructors should not do work that can fail: no I/O, no fallible
  initialization. Use a factory function or an `Init()`-style two-phase
  pattern only when a factory cannot express it; prefer factories.
- **Implicit conversions**: single-argument constructors and conversion
  operators must be marked `explicit` unless the conversion is genuinely
  meant to be implicit (rare; comment why). This includes constructors
  callable with one argument via defaults.
- **Copyable and movable types**: decide explicitly. If a type is copied,
  define copy operations consistently; if copying is expensive or
  meaningless, delete the copy operations (`= delete`) and say so. A type
  with a user-declared destructor or copy/move operations gets all of the
  special members considered (rule of five awareness). Prefer making
  expensive types move-only.
- **Structs vs classes**: `struct` only for passive data bundles with no
  invariants and no behaviour beyond trivial accessors. Anything with an
  invariant, non-trivial methods, or private data is a `class`.
- **Structs vs pairs/tuples**: prefer a named struct with named fields
  over `std::pair`/`std::tuple` whenever the elements have meaning.

## Inheritance and operators
- Inheritance is for interface implementation ("is-a" substitutability),
  not code reuse. Composition is the default. All inheritance is `public`.
- Make destructors of polymorphic base classes `virtual` (or protected
  and non-virtual by design). Derived overrides are marked `override`
  (or `final`); never rely on implicit virtual.
- Multiple inheritance only of pure interfaces (except at most one
  implementation base, in the rare sanctioned cases).
- **Operator overloading**: only where the meaning is obvious and matches
  the built-in semantics (equality, ordering, stream output for logging).
  Never overload `&&`, `||`, `,`, or unary `&`. If a reader could be
  surprised, write a named function instead.

## Access control and declaration order
- Data members are `private` (except `struct` fields and constants).
- Declaration order inside a class: `public:` first, then `protected:`,
  then `private:`. Within each section: types (`using`/nested types),
  constants, factory functions, constructors, assignment operators,
  destructor, other functions, then data members last.

## Functions
- **Parameter order**: inputs first, then outputs. Output parameters are
  pointers (so the mutation is visible at the call site: `Foo(in, &out)`);
  prefer returning values — including multiple values via a struct —
  over output parameters when the API is new.
- **Write short functions**: the guide's working number is ~40 lines;
  a longer function that cannot be split cleanly is acceptable, a longer
  one that can be is a finding.
- **Overloading** is allowed only when a reader at the call site needs no
  knowledge of the overload set to predict behaviour; overloads that
  differ only in ways invisible at the call (e.g. `int` vs `bool`
  conversions) are a finding.
- **Default arguments**: allowed on non-virtual functions when the default
  is always the same value and the pattern is already used in the class;
  **banned on virtual functions** (defaults bind statically — a classic
  trap). Never use default arguments to fake optional outputs.
- **Trailing return types** (`auto f() -> int`) only where C++ requires
  them (lambdas, some templates) or they clearly help; the default is the
  conventional front return type.
- Reference parameters are `const&` for inputs; non-const references as
  parameters are banned (use a pointer so mutation is visible).
