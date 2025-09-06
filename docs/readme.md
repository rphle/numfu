---
slug: /
---

# Getting Started with NumFu

**NumFu** is a pure, interpreted, functional programming language designed for readable and expressive code, extensibility, and ease of learning for beginners.

NumFu's simple syntax and semantics make it well-suited for educational applications, such as courses in functional programming and general programming introductions. At the same time, as its name suggests, NumFu is also ideal for exploring mathematical ideas and sketching algorithms, thanks to its native support for arbitrary-precision arithmetic.

- **Expressive syntax**: Infix operators `a + b`, spread/rest operator `...` and easy testing `---> $ == 42`
- **Arbitrary precision arithmetic** for reliable mathematical computing
- **First-class functions** with automatic partial application
- **Tail call optimization** for efficient recursive algorithms without stack overflow
- **Interactive development** with a friendly REPL and helpful errors
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

### From PyPI

```bash
# make sure you have Python >= 3.10 installed
pip install numfu-lang
```

### From Source

```bash
git clone https://github.com/dr-lego/numfu
cd numfu
make install
```

-----
## Your First NumFu Program

Create a file called `hello.nfu`:

```numfu
// hello.nfu
println("Hello, NumFu!")

// Let's do some math
let fibonacci = {n ->
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

-----
## What's Next?

- Check out the language guide: Dive deeper into NumFu with the [comprehensive documentation](guide/basic-syntax).
- Contribute: Help improve NumFu by contributing [code, documentation](https://github.com/Dr-Lego/numfu), or [bug reports](https://github.com/Dr-Lego/numfu/issues/new).
- Build Projects: Start creating your own projects and share them!
