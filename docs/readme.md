---
sidebar_position: 1
slug: /
---

# Getting Started with NumFu

**NumFu** is a functional programming language designed for readable and expressive code, extensibility, and ease of learning for beginners.

As its name suggests, NumFu is ideal for mathematical computing because it natively supports arbitrary-precision arithmetic via its powerful Python runtime.

- **Expressive syntax**: Infix operators `a + b`, spread/rest operator `...` and easy testing `---> $ == 42`
- **Arbitrary precision arithmetic** for reliable mathematical computing
- **First-class functions** with automatic partial application
- **Tail call optimization** for efficient recursive algorithms without stack overflow
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

// Native partial application
{x, y, z -> x + y + z}(_, 2)
// {x, z -> x+2+z}

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
fibonacci(5) ---> $ == 5
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
>>> [1, 2, 3, 4, 5, 6, 7] |> filter(_, {x -> x%2 == 0}) |> max
6
```
