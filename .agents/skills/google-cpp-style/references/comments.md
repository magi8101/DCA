# Comments (Google C++ Style Guide — Comments)

Comments explain **why**, contracts, and non-obvious consequences — never
a paraphrase of what the next line does. Write them for the reader who
arrives in two years without your context. If code needs a paragraph to
explain what it does, consider rewriting the code instead.

## Style
- `//` comments are the default; `/* */` only for multi-line text where
  the file already uses it (documentation blocks, license headers).
- Space after `//`, capital first letter, full stop at the end of a
  complete sentence. Be consistent inside a file.
- Comments sit above the code they describe, at the same indent. A short
  trailing comment is fine for a declaration; align trailing comments
  within a block.

## File comments
- Every file starts with a license/copyright block if the project uses
  one, followed by a file comment describing what the file provides —
  required in headers whose purpose isn't obvious from the main class.
- A header's file comment states the API's intent and any threading or
  ownership assumptions that apply file-wide.

## Class and function comments
- Every class has a comment: what it is for, its invariants, ownership
  and lifetime rules, and thread-safety — at the declaration.
- Every function declaration that is part of an API gets a comment:
  what it does, what its parameters mean (units, ranges, ownership,
  nullability), what it returns, and its error behaviour. Trivial
  accessors and obvious overrides are exempt.
- Implementation comments inside a function body explain tricky blocks,
  workarounds, and invariants — not line-by-line narration.
- Function-argument comments at call sites: for boolean or opaque
  literal arguments, name them: `Foo(/*recursive=*/true)` or, better,
  an enum. An unnamed `nullptr, false, 0` argument chain is a finding.

## Variable comments
- Class data members get a comment when their meaning, units, or
  invariants aren't obvious from the name (`int num_entries_;  // may be
  -1 before Init()`).
- Globals and statics always carry a comment saying why they exist and
  who owns them.

## TODOs and don'ts
- TODO comments are formatted `// TODO(username): description` — with an
  owner (username, email, or bug id), never a bare `// TODO`.
- Don't comment out code and leave it in the file; delete it (version
  control remembers). A kept snippet needs a comment saying why it's
  kept and when it goes.
- Don't restate the code (`i++;  // increment i`), don't leave
  change-log narration in the file ("fixed bug from last week"), and
  don't use comments to apologise for unclear code — clarify the code.
