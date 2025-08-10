---
sidebar_position: 1
slug: /
---

# Getting Started with NumFu

**NumFu** is a functional programming language designed for readable & expressive code, extensibility and ease of learning for beginners.
Moreover, as sketched by its name, NumFu is perfectly suited for mathematical computing because it supports arbitrary-precision arithmetic via its powerful python runtime natively.

- **Expressive syntax**: Infix operators `a + b`, spread/rest operator `...` and easy testing `---> _ == 42`
- **Arbitrary precision arithmetic** for reliable mathematical computing
- **First-class functions** with automatic currying partial application
- **Interactive development** with a friendly REPL and amazing errors
- **Large standard library** provided by NumFu's python bindings
- **Minimal complexity** by only having four types: `Number`, `Boolean`, `List` and `String`

-----
## Quick Example

Here's a taste of what NumFu looks like:

```numfu
// Mathematical computing
let goldenRatio = {depth ->
  let cf = {d ->
    if d <= 0 then 1
    else 1 + 1 / cf(d - 1)
  } in cf(depth)
} in goldenRatio(10)
// 1.61797752808989

// Function composition & piping
let add1 = {x -> x + 1},
    double = {x -> x * 2} in
let composed = add1 >> double in
  5 |> composed; // 12

// Built-in testing with assertions
let square = {x -> x * x} in
  square(5) ---> $ == 25; // ✓ passes
```

-----
## Installation

### From PyPI (Python ≥ 3.13)

*(not available yet)*

```bash
pip install numfu-lang
```

### From Source

```bash
git clone https://github.com/dr-lego/numfu
cd numfu
./scripts/install.sh
```

-----
## Your First NumFu Program

Create a file called `hello.nfu`:

```numfu
// hello.nfu
println("Hello, NumFu!");

// Let's do some math
{fibonacci: n ->
  if n <= 1 then n
  else fibonacci(n - 1) + fibonacci(n - 2)
}

println(format("The 10th Fibonacci number is: {}", fibonacci(10)))

// Test our function
fibonacci(5) ---> _ == 5
```

Run it:

```bash
numfu hello.nfu
```

-----
## Interactive Development

Start the REPL for interactive exploration:

```bash
numfu repl
```

```
NumFu REPL. Type 'exit' or press Ctrl+D to exit.
>>> 2 + 3 * 4
14
>>> let square = {x -> x * x} in square(7)
49
>>> filter([1, 2, 3, 4, 5, 6, 7], {x -> x%2 == 0}) |> max
6
```
