# Functions

As a functional programming language, NumFu treats functions as first-class values that can be created, passed around, and composed to build complex programs from simple parts.

-----
## Function Basics

### Creating Simple Functions

In NumFu, functions are created using lambda expressions with the syntax `{parameters -> body}`:

```numfu
{x -> x + 1}                    // Function that adds 1
{x -> x * x}                    // Function that squares a number
{name -> "Hello, " + name}      // Function that creates a greeting
```

### Calling Functions

Call functions using parentheses:

```numfu
let square = {x -> x * x} in square(5)     // 25
let greet = {name -> "Hello, " + name} in greet("NumFu")  // "Hello, NumFu"
```

### Inline Function Calls

You can call lambda expressions directly:

```numfu
{x -> x + 1}(10)               // 11
{x, y -> x * y}(3, 4)          // 12
```

-----
## Multiple Parameters

### Multiple Arguments

Functions can accept multiple parameters separated by commas:

```numfu
{x, y -> x + y}                // Addition function
{a, b, c -> a * b + c}         // Linear function
```
```numfu
let say = {name, age -> format("{} is {} years old", name, age)} in
  say("John", 42)
// John is 42 years old
```

-----
## Recursive Functions

Named functions can call themselves recursively:

```numfu
let fibonacci = {n ->
  if n <= 1 then n
  else fibonacci(n - 1) + fibonacci(n - 2)
}

fibonacci(10)    // 55
```

You can control the maximum recursion depth using the CLI argument `--rec-depth` ([see CLI reference](/docs/reference/cli#numfu-file-default-command)).

### Tail Call Optimization

NumFu automatically optimizes tail-recursive function calls, allowing you to write recursive algorithms without running into stack overflow or performance issues.

A function call is in "tail position" when it's the last operation before returning. NumFu can optimize these calls to use constant memory instead of growing the call stack:

```numfu
// Tail-recursive factorial (optimized)
let factorial = {n, acc ->
  if n <= 0 then acc
  else factorial(n - 1, acc * n)
}

// Non tail-recursive factorial (not optimized)
let factorial_slow = {n ->
  if n <= 0 then 1
  else n * factorial_slow(n - 1)  // multiplication happens after the call
}
```
The tail-recursive version works, but the non-optimized version fails with large values:
```
>>> factorial(10000, 1); factorial_slow(10000)
2.84625968091707e+35659
[at REPL:1:?]
RecursionError: maximum recursion depth exceeded
```

You can control the maximum maximum number of tail-call iterations using the CLI argument `--iter-depth` ([see CLI reference](/docs/reference/cli#numfu-file-default-command)).

-----
## Rest Parameters

### Collecting Extra Arguments

Use `...paramName` to collect remaining arguments into a list:

```numfu
{first, ...rest -> [first, rest]}(1, 2, 3, 4, 5)
// [1, [2, 3, 4, 5]]

{...args -> length(args)}(1, 2, 3)    // 3
```

Each function can only have a single rest parameter which must come at the end.


### Example

```numfu
import length, slice from "std"

let sum = {...numbers ->
  let helper = {nums, acc ->
    if length(nums) == 0 then acc
    else helper(slice(nums, 1, -1), acc + nums[0])
  } in helper(numbers, 0)
} in
  sum(1, 2, 3, 4, 5)    // 15
```

-----
## Higher-Order Functions

### Functions That Accept Functions

Functions can take other functions as parameters:

```numfu
let twice = {f, x -> f(f(x))} in
let add1 = {x -> x + 1} in
  twice(add1, 5)                // 7 (add1(add1(5)))
```

### Functions That Return Functions

Functions can return other functions:

```numfu
let makeAdder = {n -> {x -> x + n}} in
let add10 = makeAdder(10) in
  add10(5)                      // 15
```

### Function Factories

Create specialized functions using function factories:

```numfu
let makePowerFunction = {exponent ->
  {base -> base ^ exponent}
} in
let square = makePowerFunction(2) in
let cube = makePowerFunction(3) in
  [square(4), cube(3)]    // [16, 27]
```

-----
## Closures

### Capturing Environment

Functions capture variables from their surrounding environment:

```numfu
let multiplier = 10 in
let scale = {x -> x * multiplier} in
  scale(5)     50
```

### Closures Preserve Values

Even when the original scope ends, the captured values remain:

```numfu
let makeCounter = {start ->
  let current = start in
    {increment -> current + increment}
} in
let counter = makeCounter(100) in
  counter(5)    // 105
```

-----
## Examples

### Configurable Greeting
```numfu
// Create a configurable greeting function
let makeGreeting = {greeting, punctuation, name ->
  greeting + ", " + name + punctuation
} in
let casual = makeGreeting("Hi") in
let casualExcited = casual("!") in
  casualExcited("Alice")        // "Hi, Alice!"
```

### Conditional Function Selection

Choose functions based on conditions:

```numfu
let operation = "square" in
let processor = if operation == "square" then {x -> x * x}
                else if operation == "double" then {x -> x * 2}
                else {x -> x} in
  processor(6)    // 36
```

### Mathematical Functions

```numfu
import sqrt from "math"

// Distance between two points
let distance = {x1, y1, x2, y2 ->
  let dx = x2 - x1, dy = y2 - y1 in
    sqrt(dx^2 + dy^2)
} in
  distance(0, 0, 3, 4)    // 5
```

### Function Composition Function

```numfu
// Compose multiple functions
let compose = {f, g -> {x -> f(g(x))}} in

let add1 = {x -> x + 1} in
let double = {x -> x * 2} in

compose(double, add1)(5)    // 12 (double(add1(5)))
```

### Higher-Order Functions
```numfu
// Create a function that applies another function twice
let applyTwice = {f, x -> f(f(x))} in
let increment = {x -> x + 1} in
  applyTwice(increment, 10)    // 12
```

```numfu
// Create a function that creates multiplier functions
let makeMultiplier = {factor -> {x -> x * factor}} in
let triple = makeMultiplier(3) in
  triple(7)    // 21
```

### Recursive Functions
```numfu
// Factorial function
let factorial = {n ->
  if n <= 1 then 1
  else n * factorial(n - 1)
} in
  factorial(5)    // 120
```

```numfu
// Square root using Newton's method
let sqrt = {x ->
  let improve = {guess -> (guess + x / guess) / 2} in
    let iterate = {guess, n ->
      if n <= 0 then guess
      else iterate(improve(guess), n - 1)
    } in iterate(x / 2, 10)
} in sqrt(25)    // 5
```
