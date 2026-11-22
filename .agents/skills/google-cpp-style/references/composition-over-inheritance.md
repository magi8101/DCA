# Composition over inheritance

Three layers, kept separate on purpose: **Part 1** is what the Google C++
Style Guide actually rules. **Part 2** is the practice framework Magi
specified for this skill — it goes beyond the guide and is labelled as
such. **Part 3** is the syntax Google itself publishes for these patterns,
from the Abseil Tips of the Week.

## Part 1 — The guide's actual rules

- Inheritance is for interface implementation: a derived class must be
  usable anywhere the base is expected (a true "is-a", substitutable).
  Using inheritance just to reuse a base class's code is a finding —
  prefer composition (hold the other object as a member and delegate).
- All inheritance is `public`. If you find yourself wanting `private`
  inheritance for reuse, that is the composition signal.
- Composition is often more appropriate than inheritance; when both
  work, the guide's stated bias is to ask whether the relationship is
  really substitutability or just shared machinery.
- Multiple inheritance is allowed only when at most one base has an
  implementation; the rest must be pure interface classes (named with an
  `Interface`-flavoured convention in Google code).
- A class that is a base must have a virtual destructor (or a protected
  non-virtual one by deliberate design), and overrides are marked
  `override`. If a class is not meant to be a base, say so with `final`.
- Operator interfaces and interface classes stay small; the guide
  discourages deep hierarchies and inheritance for factoring out a few
  common lines.

## Part 2 — Practice beyond the guide (Magi's framework)

These rows are design guidance for new code, not guide rulings. Reviewers
should cite them as this skill's practice, not as "the guide says".

| Area | Practice |
| --- | --- |
| Inheritance | Avoid implementation inheritance; inherit interfaces, not behaviour. |
| Composition | Prefer composing smaller components into a whole over extending a base. |
| Polymorphism | Prefer function objects, `std::variant`, or explicit dispatch over virtual hierarchies when the set of cases is closed or the behaviour is a strategy. |
| Interfaces | Use lightweight contracts — a concept or a callable — sized to what the consumer actually calls. DCA bans virtual hierarchies, so a concept or a table of function pointers is the contract; reserve an abstract class for a runtime boundary the project has explicitly accepted. |
| Code reuse | Prefer delegation: wrap the component and forward only the operations you mean to expose. |
| State management | Keep state ownership explicit: the composed member's owner is visible in the type (value member, `std::unique_ptr`), never a bare pointer whose owner is folklore. |
| Dependencies | Prefer dependency injection: pass collaborators in through the constructor (as references or `unique_ptr`) instead of constructing or reaching for globals inside the class. |

## Part 3 — The syntax Google publishes (Abseil Tips of the Week)

- **Factories instead of `Init()`** (Tip #42, "Prefer Factory Functions to
  Initializer Methods"): when construction can fail or do work, expose a
  static factory — `static absl::StatusOr<Foo> Foo::Create(...)` (outside
  Google, `std::expected`/a status type of the project's) — and keep the
  constructor trivial. Two-phase `Init()` methods are the anti-pattern
  this replaces.
- **Delegating and inheriting constructors** (Tip #74): a constructor
  that repeats another's work delegates — `Foo(int x) : Foo(x, 0) {}` —
  and a derived class that wants the base's constructors wholesale says
  `using Base::Base;` instead of writing forwarding constructors by hand.
  Use these instead of shared `Init()` helpers inside the class.
- **Nonmember interfaces** (Tip #99, "Nonmember Interface Etiquette"):
  functions that don't need private access belong outside the class, as
  nonmember (often non-friend) functions in the same namespace. A smaller
  member surface means fewer things coupled to the class's internals —
  this is the interface-shrinking half of composition.
- **What a parameter type promises** (Tip #188, "Be Careful With
  Smart-Pointer Function Parameters", and Tip #234, "Pass by Value, by
  Pointer, or by Reference?"): the parameter type is the contract —
  `std::unique_ptr<T>` by value means "I take ownership", a raw pointer
  or reference means "I borrow", `const T&` for read-only input,
  `std::shared_ptr` by value only for genuinely shared ownership. When
  composing components, pass them by the type that states the ownership
  you mean; never accept a smart pointer just to call `.get()` on it.
