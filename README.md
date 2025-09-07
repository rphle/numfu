![](https://raw.githubusercontent.com/rphle/numfu/main/images/banner.png)

![PyPI - Version](https://img.shields.io/pypi/v/numfu-lang)
![PyPI - License](https://img.shields.io/pypi/l/numfu-lang)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/numfu-lang)
![PyPI Downloads](https://img.shields.io/pypi/dm/numfu-lang)
[![Docs](https://img.shields.io/badge/docs-NumFu-brightgreen)](https://rphle.github.io/numfu/)
![GitHub stars](https://img.shields.io/github/stars/rphle/numfu?style=social)


# NumFu Programming Language

**NumFu** is a pure, interpreted, functional programming language designed for readable & expressive code, extensibility, and ease of learning for beginners.

NumFu's simple syntax and semantics make it well-suited for educational applications, such as courses in functional programming and general programming introductions. At the same time, as its name suggests, NumFu is also ideal for exploring mathematical ideas and sketching algorithms, thanks to its native support for arbitrary-precision arithmetic.

## Features

- **Arbitrary Precision Arithmetic** - Reliable mathematical computing powered by Python's mpmath
- **First-Class Functions** - Automatic currying, partial application, and function composition
- **Expressive Syntax** - Infix operators, spread/rest operators, and lots of syntactic sugar
- **Tail Call Optimization** for efficient recursive algorithms without stack overflow
- **Interactive Development** - Friendly REPL and helpful error messages
- **Minimal Complexity** - Only four core types: `Number`, `Boolean`, `List`, and `String`
- **Python Integration** - Large & reliable standard library through NumFu's Python runtime
- **Extensible** - NumFu is written entirely in Python with the goal of being extensible and easy to understand.

## Quick Start

### Installation

#### From PyPI
```bash
pip install numfu-lang
```

#### From Source
```bash
git clone https://github.com/rphle/numfu
cd numfu
make install
```

### Hello NumFu!

Create `hello.nfu`:
```numfu
import sqrt from "math"

// Mathematical computing with arbitrary precision
let golden = {depth ->
  let recur =
    {d -> if d <= 0 then 1 else 1 + 1 / recur(d - 1)}
  in recur(depth)
} in golden(10) // ≈ 1.618

// Function composition & piping
let add1 = {x -> x + 1},
    double = {x -> x * 2}
in 5 |> (add1 >> double) // 12

// Partial Application
{a, b, c -> a+b+c}(_, 5, _)
// {a,c -> a+5+c}

// Assertions
sqrt(49) ---> $ == 7

// Built-in testing with assertions
let square = {x -> x * x} in
  square(7) ---> $ == 49  // ✓ passes
```

Run it:
```bash
numfu hello.nfu
```

### Interactive REPL

```bash
numfu repl
```

```
NumFu REPL. Type 'exit' or press Ctrl+D to exit.
>>> 2 + 3 * 4
14
>>> let square = {x -> x * x} in square(7)
49
>>> import max from "math"
>>> [1, 2, 3, 4, 5, 6, 7] |> filter(_, {x -> x%2 == 0}) |> max
6
```

## 📖 Documentation

- **[Language Guide](https://rphle.github.io/numfu/docs/)** - Complete language tutorial & reference
- **[Stdlib Reference](https://rphle.github.io/numfu/docs/reference/stdlib)** - All built-in modules and utilities
- **[CLI Reference](https://rphle.github.io/numfu/docs/reference/cli)** - Command-line interface guide

> [!NOTE]
> As a language interpreted in Python, which is itself an interpreted language, NumFu is not especially fast. Therefore, it is not recommended for performance-critical applications or large-scale projects. However, NumFu has not yet been thoroughly optimized so you can expect some performance improvements in the future.

## Language Overview

### Functions with Automatic Partial Application

Functions are defined using `{a, b, ... -> ...}` syntax. They're automatically partially applied, so if you supply fewer arguments than expected, the function returns a new function that expects the remaining arguments:

```numfu
let fibonacci = {n ->
    if n <= 1 then n
    else fibonacci(n - 1) + fibonacci(n - 2)
}
fibonacci(10)
```

### Function Syntax Reconstruction

When functions (even partially applied ones) are printed or cast to strings, NumFu reconstructs readable syntax!

```numfu
>>> {a, b, c -> a + b + c}(_, 5)
{a, c -> a+5+c}  // Functions print as readable syntax!
```

### Function Composition and Piping

```numfu
let add1 = {x -> x + 1},
    double = {x -> x * 2}
in 5 |> (add1 >> double); // 12

// List processing
[5, 12, 3] |> filter(_, _ > 4) |> map(_, _ * 2)
// [10, 24]
```

### Spread/Rest Operators

Support for variable-length arguments and destructuring:

```numfu
import length from "std"

{...args -> length(args)}(1, 2, 3)    // 3

{first, ...rest -> [first, ...rest]}(1, 2, 3, 4, 5)
// [1, 2, 3, 4, 5]
```

### Module System

Export and import functions and values between modules. Supports path imports and directory modules with `index.nfu`:

```numfu
import sqrt from "math"
import * from "io"

let greeting = "Hello, " + input("What's your name? ")

export distance = {x1, y1, x2, y2 ->
    let dx = x2 - x1, dy = y2 - y1 in
    sqrt(dx^2 + dy^2)
}

export greeting
```

### Arbitrary Precision Arithmetic

All numbers use Python's `mpmath` for reliable mathematical computing without floating point errors. Precision can be configured via CLI arguments:

```numfu
import pi, degrees from "math"

0.1 + 0.2 == 0.3 // true
degrees(pi / 2) == 90 // true
```

### Precise Error Messages

Errors always point to the exact line and column with proper preview and clear messages:

```
[at examples/bubblesort.nfu:11:17]
[11]           else if workingarr[i] > workingArr[i + ...
                       ^^^^^^^^^^
NameError: 'workingarr' is not defined in the current scope
```
```
[at tests/functions.nfu:36:20]
[36]   let add1 = {x -> x + "lol"} in
                          ^
TypeError: Invalid argument type for operator '+': argument 2 must be Number, got String
```

## 🛠️ Development

### Prerequisites

- Python ≥ 3.10

### Setup Development Environment

```bash
git clone https://github.com/rphle/numfu
cd numfu
make dev
```
The `make dev` command also installs Pyright and Ruff via Pip. To format code and check types, it is strongly recommended to run both `ruff check --fix` and `pyright` before committing.

## Building NumFu

```
make build
```

NumFu contains built-ins written in NumFu itself (src/numfu/stdlib/builtins.nfu).
`make build` first installs NumFu without the built-ins, then parses and serializes the file, and finally performs a full editable install. The script also builds NumFu and creates wheels.

### Building Documentation

```bash
cd docusaurus && npm i && cd .. # make sure to install dependencies

make serve  # local preview
make docs   # build to 'docs-build'
```

## Project Structure

```
numfu/
├── src/numfu/
│   ├── __init__.py         # Package exports
│   ├── _version.py         # Version & metadata
│   ├── classes.py          # Basic dataclasses
│   ├── parser.py           # Lark-based parser & AST generator
│   ├── interpreter.py      # Complete Interpreter
│   ├── modules.py          # Import/export & module resolving
│   ├── ast_types.py        # AST node definitions
│   ├── builtins.py         # Built-in functions
│   ├── cli.py              # Command-line interface
│   ├── repl.py             # Interactive REPL
│   ├── errors.py           # Error handling & display
│   ├── typechecks.py       # Built-in type system
│   ├── reconstruct.py      # Code reconstruction for printing
│   ├── grammar/            # Lark grammar files
│   └── stdlib/             # Standard library modules
├── docs/                   # Language documentation
│   ├── guide/              # User guides
│   └── reference/          # Reference
├── docusaurus/             # Docusaurus website
├── tests/                  # Test files
├── scripts/                # Build and utility scripts
└── pyproject.toml          # Configuration
```

## Testing

NumFu is tested with over 300 tests covering core features, edge cases, and real-world examples — including most snippets from the documentation. Tests are grouped by category and include handwritten cases as well as tests generated by LLMs (mostly Claude Sonnet 4).

Every test is self-validating using assertions and fails with an error if the output isn’t exactly as expected.

To run all tests from the `tests` folder:

```bash
make test
```

## Contributing

Found a bug or have an idea? [Open an issue](https://github.com/rphle/numfu/issues).

Want to contribute code?
- Check existing issues and [TODO.md](https://github.com/rphle/numfu/blob/main/TODO.md) for open tasks.
- Run all tests before committing.
- Please consider running `ruff check` and `pyright` to format code and check types before committing.
- Pull requests are welcome!


## License

This project is licensed under Apache License 2.0 - see the [LICENSE](https://github.com/rphle/numfu/blob/main/LICENSE) file for details.
